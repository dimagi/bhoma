from couchdbkit.ext.django.forms import DocumentForm
from bhoma.apps.patient.models import CPatient

class PatientForm(DocumentForm):
    
    
    class Meta:
        document = CPatient
        exclude = ["clinic_ids", ]
    