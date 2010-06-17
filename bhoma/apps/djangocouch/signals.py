from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from couchdbkit.ext.django.loading import get_db
from bhoma.apps.djangocouch.models import DemoModel
from couchdbkit.resource import ResourceConflict, ResourceNotFound
import logging

def couch_post_save(sender, instance, created, **kwargs): 
    """
    Signal for saving your model to a couchdb.  
    
    Assumptions:
    
        The instance of the model passed in should be an extension of CouchModel
        The inherited _id field never changes after writing
        You are always willing to overwrite the latest changes without warning
      
    """
    if not hasattr(instance, "_id"):
        raise Exception("Your model must extend CouchModel in order to use this signal!")
    
    if not instance._id:
        # this shouldn't be possible unless they've hacked the UUIDField
        raise Exception("The couch_id field should always be set before saving to django!")
    
    content_type = ContentType.objects.get_for_model(instance)
    try:
        db = get_db(content_type.app_label)
    except KeyError:
        raise Exception("You must initialize your django app with a couchdb "
                        "in your settings to use these models!")
    
    instance_dict = instance.to_dict()
    if not created:
        try:
            previous_doc = db.get(instance._id)
            instance_dict["_rev"] = previous_doc["_rev"]
        except ResourceNotFound:
            logging.warn("Expected resource for doc %s but was missing..." %\
                         instance._id)
            
    # arbitrarily try thrice before failing
    tries = 0
    success = False
    while tries < 3 and not success:
        try:
            response = db.save_doc(instance_dict)
            success = True
        except ResourceConflict, e:
            logging.warn("Resource conflict for doc %s, rev %s.  Trying again..." %\
                         (instance._id, instance_dict.get("_rev")))
            tries = tries + 1
            # maybe we had a parallel update
            previous_doc = db.get(instance._id)
            instance_dict["_rev"] = previous_doc["_rev"]

post_save.connect(couch_post_save, DemoModel)