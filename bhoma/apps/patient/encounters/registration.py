import os
from bhoma.apps.encounter import EncounterTypeBase
from bhoma.apps.xforms.models import XForm
from bhoma.apps.encounter.models import EncounterType

NAMESPACE = "http://openrosa.org/bhoma/registration"
NAME      = "registration"
FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "xforms")
FILE_NAME = "registration.xml"

class RegistrationEncounter(EncounterTypeBase):
    """A registration encounter"""
    
    def __init__(self):
        matches = XForm.objects.filter(namespace=NAMESPACE).order_by("-version")
        if matches.count() > 0:
            self.xform = matches[0]
        else:
            # TODO: is this sneaky lazy loading a reasonable idea?
            filename = os.path.join(FILE_PATH, FILE_NAME)
            self.xform = XForm.from_file(filename)
        
        try:
            self._type = EncounterType.objects.get(xform=self.xform)
        except EncounterType.DoesNotExist:
            self._type = EncounterType.objects.create(xform=self.xform, name=NAME)
        
        
    @property
    def type(self):
        return self._type
    
    def start_form_entry(self, **kwargs):
        """Called immediately before form entry starts."""
        pass
    
    def finish_form_entry(self, instance, **kwargs):
        """Called immediately after form entry completes."""
        pass
    
    