from django.db.models.signals import post_save
from django.conf import settings
from bhoma.apps.profile.models import BhomaUserProfile
from djangocouchuser.signals import couch_user_post_save
from django.contrib.auth.models import SiteProfileNotAvailable, User
import logging

def user_post_save(sender, instance, created, **kwargs): 
    """
    The user post save signal, to auto-create our Profile
    """
    if not created:
        try:
            instance.get_profile().save()
            return
        except BhomaUserProfile.DoesNotExist:
            logging.warn("There should have been a profile for "
                         "%s but wasn't.  Creating one now." % instance)
        except SiteProfileNotAvailable:
            raise
    
    profile, created = BhomaUserProfile.objects.get_or_create(user=instance,
                                                              clinic_id=settings.BHOMA_CLINIC_ID)
    if not created:
        # magically calls our other save signal
        profile.save()
        
post_save.connect(user_post_save, User)        
post_save.connect(couch_user_post_save, BhomaUserProfile)