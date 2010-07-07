from __future__ import absolute_import
from bhoma.apps.locations.models import Location
from django.db import models
from django.contrib.contenttypes.models import ContentType
from bhoma.apps.djangoplus.models import UUIDModel


# last model that needs migration.
class Address(UUIDModel):
    """An address"""
    # person = models.ForeignKey(Person)
    house_description = models.CharField(max_length=300)
    village = models.CharField(max_length=100)
    chief = models.CharField(max_length=100)
    zone = models.ForeignKey(Location)
    # TODO: chw?

    class Meta:
        app_label = 'patient'
    
