from bhoma.apps.xforms import CXFormInstance
from bhoma import const
from bhoma.apps.patient.models import CPatient

def delete_all_patients():
    for pat in CPatient.view(const.VIEW_PATIENT_BY_BHOMA_ID, reduce=False, include_docs=True).all():
        pat.delete()
        
def delete_all_xforms():
    for form in CXFormInstance.view(const.VIEW_XFORMS_BY_XMLNS, include_docs=True).all():
        form.delete()
        