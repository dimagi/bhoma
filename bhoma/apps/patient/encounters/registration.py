import os
from bhoma.apps.encounter import EncounterTypeBase
from bhoma.apps.xforms.models import XForm
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.xforms.models.django import XFormCallback

NAMESPACE = "http://openrosa.org/bhoma/registration"
NAME      = "registration"
FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "xforms")
FILE_NAME = "registration.xml"

class RegistrationEncounter(EncounterTypeBase):
    """A registration encounter"""
    
    def __init__(self):
        fail = False
        
        matches = XForm.objects.filter(namespace=NAMESPACE).order_by("-version")
        if matches.count() > 0:
            self.xform = matches[0]
        else:
            fail = True

        try:
            self._type = EncounterType.objects.get(xform=self.xform)
        except EncounterType.DoesNotExist:
            fail = True
        
        
        if fail:
            # should we be less harsh?
            raise Exception("No XForm found! Either the application wasn't " \
                            "bootstrapped properly or the database entry was " \
                            "deleted. Please restart the server.")
        
    @property
    def type(self):
        return self._type
    
    def start_form_entry(self, **kwargs):
        """Called immediately before form entry starts."""
        pass
    
    def finish_form_entry(self, instance, **kwargs):
        """Called immediately after form entry completes."""
        pass

def form_complete(instance):
    print "form complete! %s" % instance
    
def bootstrap():
    matches = XForm.objects.filter(namespace=NAMESPACE).order_by("-version")
    if matches.count() > 0:
        xform = matches[0]
    else:
        # TODO: is this sneaky lazy loading a reasonable idea?
        filename = os.path.join(FILE_PATH, FILE_NAME)
        xform = XForm.from_file(filename)
    
    try:
        type = EncounterType.objects.get(xform=xform)
    except EncounterType.DoesNotExist:
        type = EncounterType.objects.create(xform=xform, name=NAME)
    
    # delete and recreate the callbacks automatically
    XFormCallback.objects.filter(xform=xform).delete()
    XFormCallback.objects.create(xform=xform, 
                                 callback="bhoma.apps.patient.encounters.registration.form_complete")
    