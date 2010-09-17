from bhoma.apps.djangocouch.exceptions import ModelPreconditionNotMet
from django.contrib.contenttypes.models import ContentType
from couchdbkit.ext.django.loading import get_db
from django.db.models.fields.related import ManyToManyField, ForeignKey
from bhoma.apps.djangocouchuser import const
from couchdbkit.resource import ResourceNotFound, ResourceConflict
from couchdbkit.ext.django.schema import dict_to_json as couchdbkit_dict_to_json,\
    Document, value_to_json
import logging
from django.conf import settings

DEFAULT_DJANGO_TYPE_KEY = "django_type"
MAX_COUCH_SAVE_TRIES    = 3

def futon_url(object_id):
    def strip_credentials(server):
        # super janky
        if "://" in server and "@" in server:
            return "%s://%s" % (server[0:server.index("://")], server[server.index("@") + 1:])
    return "%s/_utils/document.html?%s/%s" % \
                                (strip_credentials(settings.BHOMA_COUCH_SERVER), 
                                 settings.BHOMA_COUCH_DATABASE_NAME,
                                 object_id)

def model_to_dict(instance, fields=None, exclude=None, 
                  django_type_key=DEFAULT_DJANGO_TYPE_KEY):
    """
    Convert an instance of a django model to a dictionary / document
    object 
    """
    # implementation copied/modified from:
    # django.forms.models.model_to_dict 
    # we still want uneditable fields included here
    opts = instance._meta
    data = {}
    for f in opts.fields + opts.many_to_many:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primry key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # for now, use a list of pks, not object instances.
                data[f.name] = [obj.pk for obj in f.value_from_object(instance)]
        else:
            # try to serialize if if possible
            data[f.name] = value_to_json(f.value_from_object(instance))

    ct = ContentType.objects.get_for_model(instance)
    # include the model class as well
    data[django_type_key] = "%s.%s" % (ct.app_label, ct.model)
    return data 
    

def model_to_doc(instance, fields=None, exclude=None, 
                  django_type_key=DEFAULT_DJANGO_TYPE_KEY):
    """
    Convert an instance of a django model to a dictionary / document
    object 
    """
    # implementation copied/modified from:
    # django.forms.models.model_to_dict 
    # we still want uneditable fields included here
    to_return = Document()
    opts = instance._meta
    data = {}
    for f in opts.fields + opts.many_to_many:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primry key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # MultipleChoiceWidget needs a list of pks, not object instances.
                # data[f.name] = [obj.pk for obj in f.value_from_object(instance)]
                setattr(to_return, f.name,
                        [obj.pk for obj in f.value_from_object(instance)])
        elif isinstance(f, ForeignKey):
            obj = getattr(instance, f.name, None)
            setattr(to_return, f.name,
                    obj.pk if obj is not None else None)
        else:
            setattr(to_return, f.name,f.value_from_object(instance))
            # data[f.name] = f.value_from_object(instance)

    ct = ContentType.objects.get_for_model(instance)
    # include the model class as well
    # data[django_type_key] = "%s.%s" % (ct.app_label, ct.model)
    # return data
    setattr(to_return, django_type_key, "%s.%s" % (ct.app_label, ct.model))
    return to_return

def dict_to_json(dict):
    return couchdbkit_dict_to_json(dict)
    
def get_db_for_instance(instance):
    """
    Get the database for a model instance, even if it's not
    an explicit couch model, based on the definition in
    the app's settings.  
    
    Returns None if no database is found.
    """
    content_type = ContentType.objects.get_for_model(instance)
    try:
        return get_db(content_type.app_label)
    except KeyError:
        return None
    

def check_model_preconditions_for_save(instance):
    """
    Checks that a django model is ready to be saved in couch,
    ensuring it extends the right model, has a user field, a
    referenced database, etc.
    
    Fails by raising an exception.
    
    Returns a reference to the database for the instance for convenience
    """
    if not hasattr(instance, "_id"):
        raise ModelPreconditionNotMet("Your model must extend CouchModel in order to use this signal!")
    
    if not instance._id:
        # this shouldn't be possible unless they've hacked the UUIDField
        raise ModelPreconditionNotMet("The couch_id field should always be set before saving to django!")
    
    
    db = get_db_for_instance(instance)
    if db is None:
        raise ModelPreconditionNotMet("You must initialize your django app with a couchdb "
                                      "in your settings to use these models!")
    
    return db

def save_dict(db, instance_dict, created):
    """
    Saves a dictionary of values to the couch database.  
    
    This is basically the dame as db.save() with a force option turned on and
    better logging.
    """
    if not created:
        try:
            previous_doc = db.get(instance_dict[const.COUCH_ID])
            instance_dict[const.COUCH_REV] = previous_doc[const.COUCH_REV]
        except ResourceNotFound:
            logging.warn("Expected resource for doc %s but was missing..." %\
                         instance_dict[const.COUCH_ID])
            
    # arbitrarily try thrice before failing
    tries = 0
    while tries < MAX_COUCH_SAVE_TRIES:
        try:
            response = db.save_doc(instance_dict)
            logging.debug("Saved %s, got back %s" % \
                          (instance_dict[const.COUCH_ID], response))
            return db.get(instance_dict[const.COUCH_ID])
        except ResourceConflict, e:
            logging.warn("Resource conflict for doc %s, rev %s.  %s. Trying again..." %\
                         (instance_dict[const.COUCH_ID], e, instance_dict.get("_rev")))
            tries = tries + 1
            # maybe we had a parallel update
            previous_doc = db.get(instance_dict[const.COUCH_ID])
            instance_dict[const.COUCH_REV] = previous_doc[const.COUCH_REV]
    