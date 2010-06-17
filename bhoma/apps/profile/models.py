from django.db import models
from django.conf import settings
from bhoma.apps.djangocouchuser.models import CouchUserProfile

class BhomaUserProfile(CouchUserProfile):
    """
    The Bhoma Profile object, which saves the user data in couch along
    with annotating the additional fields we need for BHOMA
    """
    clinic_id = models.CharField(max_length=100, default=settings.BHOMA_CLINIC_ID)
    
# load our signals.
import bhoma.apps.profile.signals 