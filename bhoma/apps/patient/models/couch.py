from __future__ import absolute_import

import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import *
from bhoma.apps.encounter.models import Encounter
from couchdbkit.schema.properties_proxy import SchemaListProperty
from bhoma.apps.case.models import CCase


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
GENDER_MALE = "m"
GENDER_FEMALE = "f"
GENDERS = (GENDER_MALE, GENDER_FEMALE)

class CPatient(Document):
    first_name = StringProperty(required=True)
    middle_name = StringProperty()
    last_name = StringProperty(required=True)
    birthdate = DateProperty(required=True)
    birthdate_estimated = BooleanProperty()
    gender = StringProperty(required=True)
    clinic_ids = StringListProperty()
    encounters = SchemaListProperty(Encounter())
    cases = SchemaListProperty(CCase())
    
    class Meta:
        app_label = 'patient'

    def __unicode__(self):
        return "%s %s (%s, DOB: %s)" % (self.first_name, self.last_name,
                                        self.gender, self.birthdate)
    def update_cases(self, case_list):
        """
        Update cases attached to a patient instance, or add
        them if they are new
        """
        for touched_case in case_list:
            found_index = len(self.cases)
            for i in range(len(self.cases)):
                pat_case = self.cases[i]
                if pat_case.case_id == touched_case.case_id:
                    found_index = i
            # replace existing cases with the same id if we find them
            # this defaults to appending on the end of the list
            self.cases[found_index] = touched_case
        
class CPhone(Document):
    patient = SchemaProperty(CPatient())
    is_default = BooleanProperty()
    number = StringProperty()
    
    class Meta:
        app_label = 'patient'
