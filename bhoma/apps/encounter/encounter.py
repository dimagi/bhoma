from bhoma.apps.xforms.models import XForm


class EncounterTypeBase(object):
    """Base class for an encounter type.  This should be extended by 
       a specific encounter to do form-specific actions."""
       
    @property
    def type(self):
        """Get the type associated with this"""
        raise NotImplementedError("Subclasses should override this!")
    
    def start_form_entry(self, **kwargs):
        """Called immediately before form entry starts."""
        pass
    
    def finish_form_entry(self, instance, **kwargs):
        """Called immediately after form entry completes."""
        pass
    

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
    
        