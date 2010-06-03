from __future__ import absolute_import

import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import *


"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.
"""

class CDistrict(Document):
    slug = StringProperty()
    name = StringProperty()
    
    class Meta:
        app_label = 'patient'

class CClinic(Document):
    slug = StringProperty()
    name = StringProperty()
    district_id = StringProperty()
    
    class Meta:
        app_label = 'patient'

# you can do choices=GENDERS, but it's still buggy and doesn't play nice
# with form validation yet, so holding off
# GENDERS = ("m", "f")

class CPatient(Document):
    first_name = StringProperty(required=True)
    middle_name = StringProperty()
    last_name = StringProperty(required=True)
    birthdate = DateProperty(required=True)
    birthdate_estimated = BooleanProperty()
    gender = StringProperty(required=True)
    clinic_id = StringProperty()
    
    class Meta:
        app_label = 'patient'

    def __unicode__(self):
        return "%s %s (%s, DOB: %s)" % (self.first_name, self.last_name,
                                        self.gender, self.birthdate)
    
class CPhone(Document):
    patient = SchemaProperty(CPatient())
    is_default = BooleanProperty()
    number = StringProperty()
    
    class Meta:
        app_label = 'patient'

# single time bootstrap
# Because the couch extension doesn't seem to work with django out of the box

"""  
# server object
server = Server()

# create database
database = server.get_or_create_db(settings.COUCH_DATABASE_NAME)

# bind models
# associate objects to the db
CDistrict.set_db(database)
CClinic.set_db(database)
CPatient.set_db(database)
"""