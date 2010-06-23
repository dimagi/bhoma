from __future__ import absolute_import
from bhoma.apps.locations.models import Location
from django.db import models
from django.contrib.contenttypes.models import ContentType
from bhoma.apps.djangoplus.models import UUIDModel


class PersonType(UUIDModel):
    """
    A type of person, like a patient or a bus driver
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(unique=True, max_length=255)
    model = models.ForeignKey(ContentType, null=True, blank=True,
                              help_text="If specified, the model you can use "
                                        "to get more information about this "
                                        "person")
    class Meta:
        app_label = 'patient'

    def __unicode__(self):
        return self.name


GENDERS = (("m", "male"),("f", "female")) 

class Person(UUIDModel):
    """A person"""
    
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birthdate = models.DateField()
    birthdate_estimated = models.BooleanField()
    gender = models.CharField(max_length=1, choices=GENDERS)
    types = models.ManyToManyField(PersonType, blank=True)
    
    class Meta:
        app_label = 'patient'

class Phone(UUIDModel):
    person = models.ForeignKey(Person, null=True, blank=True)
    is_default = models.BooleanField(default=True)
    number = models.CharField(max_length=30)

    class Meta:
        app_label = 'patient'
    

class Address(UUIDModel):
    """An address"""
    person = models.ForeignKey(Person)
    house_description = models.CharField(max_length=300)
    village = models.CharField(max_length=100)
    chief = models.CharField(max_length=100)
    zone = models.ForeignKey(Location)
    # TODO: chw?

    class Meta:
        app_label = 'patient'
    
class Patient(Person):
    """A patient."""
    # TODO: make a unique field type for this?
    patient_id = models.CharField(max_length=20)
    
    class Meta:
        app_label = 'patient'
