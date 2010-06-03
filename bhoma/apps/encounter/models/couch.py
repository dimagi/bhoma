from __future__ import absolute_import

from couchdbkit.ext.django.schema import *
from bhoma.apps.patient.models import CPatient

"""
Couch models go here.  
"""

class Encounter(Document):
    created = DateTimeProperty(required=True)
    edited = DateProperty(required=True)
    type = StringProperty()
    patient = SchemaProperty(CPatient())
    is_deprecated = BooleanProperty()
    previous_encounter_id = StringProperty()
    
    class Meta:
        app_label = 'encounter'

    def __unicode__(self):
        return "%s (%s)" % (self.type, self.created)
    
        