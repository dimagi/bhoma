from django.dispatch import Signal
from bhoma.apps.xforms.signals import xform_saved

form_added_to_patient = Signal(providing_args=["patient", "form"])

def form_saved(sender, form, **kwargs):
    """
    Checks every form that's saved for a patient id.  If it finds one
    raises a second signal that a form has been added to a patient.
    """
    patient_id = form.xpath("case/patient_id")
    
    from bhoma.apps.patient.models import CPatient
    if patient_id:
        patient = CPatient.get(patient_id)
        form_added_to_patient.send(sender="patient", patient=patient, form=form)
        
        
    

xform_saved.connect(form_saved)