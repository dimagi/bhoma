from django.db.models.signals import post_save
from bhoma.apps.djangocouch.models import DemoModel
from couchdbkit.resource import ResourceConflict, ResourceNotFound
import logging
from bhoma.apps.djangocouch.utils import check_model_preconditions_for_save

def couch_post_save(sender, instance, created, **kwargs): 
    """
    Signal for saving your model to a couchdb.  
    
    Assumptions:
    
        The instance of the model passed in should be an extension of CouchModel
        The inherited _id field never changes after writing
        You are always willing to overwrite the latest changes without warning
      
    """
    
    db = check_model_preconditions_for_save(instance)
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
    print db
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
    print "succes: %s" % success
    
post_save.connect(couch_post_save, DemoModel)