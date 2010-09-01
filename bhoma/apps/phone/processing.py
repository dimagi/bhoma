from bhoma.apps.patient.models.couch import CPatient
    
def get_patient_from_form(form):
    patient_id = form.xpath("case/patient_id")
    if patient_id:
        return CPatient.get(patient_id)
    return None
            
