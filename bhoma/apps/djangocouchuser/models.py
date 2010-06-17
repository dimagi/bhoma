from django.db import models
from django.contrib.auth.models import User
from bhoma.apps.djangocouch.models import CouchModel

class CouchUserProfile(CouchModel):
    """
    A user profile to synchronize your django users in couchdb
    """
    
    # This is the only required field
    user = models.ForeignKey(User, unique=True)
    
    class Meta:
        abstract = True

# load our signals.
import bhoma.apps.djangocouchuser.signals 