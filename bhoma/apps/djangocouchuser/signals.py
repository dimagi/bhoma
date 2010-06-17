from django.contrib.contenttypes.models import ContentType
from bhoma.apps.djangocouch.utils import check_model_preconditions_for_save,\
    model_to_dict, save_dict, model_to_doc
from bhoma.apps.djangocouch.exceptions import ModelPreconditionNotMet
from bhoma.apps.djangocouchuser import const

def couch_user_post_save(sender, instance, created, **kwargs): 
    """
    Signal for saving your user and profile to a couchdb.  
    
    Assumptions:
    
        The instance of the model passed in should be an extension of CouchModel
        The inherited _id field never changes after writing
        You are always willing to overwrite the latest changes without warning
      
    """
    
    db = check_model_preconditions_for_save(instance)
    
    user = getattr(instance, "user", None)
    if user is None:
        raise ModelPreconditionNotMet("You are saving a profile without an attached user!")
    
    instance_dict = model_to_dict(instance)
    # now change the user to actually be a full user dict, not just the 
    # pk.  
    user_dict = model_to_dict(user)
    instance_dict[const.USER_KEY] = user_dict
    save_dict(db, instance_dict, created)
    
