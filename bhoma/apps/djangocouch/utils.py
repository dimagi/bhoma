from bhoma.apps.djangocouch.exceptions import ModelPreconditionNotMet
from django.contrib.contenttypes.models import ContentType
from couchdbkit.ext.django.loading import get_db
from django.db.models.fields.related import ManyToManyField

DEFAULT_DJANGO_TYPE_KEY = "django_type"

def model_to_dict(instance, fields=None, exclude=None, 
                  django_type_key=DEFAULT_DJANGO_TYPE_KEY):
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
                # MultipleChoiceWidget needs a list of pks, not object instances.
                data[f.name] = [obj.pk for obj in f.value_from_object(instance)]
        else:
            data[f.name] = f.value_from_object(instance)

    ct = ContentType.objects.get_for_model(instance)
    # include the model class as well
    data[django_type_key] = "%s.%s" % (ct.app_label, ct.model)
    return data


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