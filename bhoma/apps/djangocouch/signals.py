from django.db.models.signals import post_save
from bhoma.apps.djangocouch.models import DemoModel
from bhoma.apps.djangocouch.utils import check_model_preconditions_for_save,\
    save_dict, model_to_dict

def couch_post_save(sender, instance, created, **kwargs): 
    """
    Signal for saving your model to a couchdb.  
    
    Assumptions:
    
        The instance of the model passed in should be an extension of CouchModel
        The inherited _id field never changes after writing
        You are always willing to overwrite the latest changes without warning
      
    """
    
    db = check_model_preconditions_for_save(instance)
    instance_dict = model_to_dict(instance)
    save_dict(db, instance_dict, created)
    
post_save.connect(couch_post_save, DemoModel)