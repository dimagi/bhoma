from bhoma.apps.djangoplus.fields import UUIDField
from django.db import models

class UUIDModel(models.Model):
    """
    A basic model to use uuids instead of integer ids as primary keys
    """
    
    id = UUIDField(primary_key=True)
    
    class Meta:
        abstract = True
