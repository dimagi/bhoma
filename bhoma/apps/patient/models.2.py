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

class CClinic(Document):
    slug = StringProperty()
    name = StringProperty()
    district_id = StringProperty()
    
class CPatient(Document):
    first_name = StringProperty()
    middle_name = StringProperty()
    last_name = StringProperty()
    birthdate = DateProperty()
    birthdate_estimated = BooleanProperty()
    gender = StringProperty()
    clinic_id = StringProperty()
    
    def __str__(self):
        return "%s %s (%s, DOB: %s)" % (self.first_name, self.last_name,
                                        self.gender, self.birthdate)

"""

# single time bootstrap

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