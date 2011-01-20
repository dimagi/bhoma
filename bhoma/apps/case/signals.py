from datetime import datetime
from bhoma.apps.patient.signals import patient_updated
from bhoma.apps.case.const import Outcome

def update_patient_deceased_status(sender, patient_id, **kwargs):
    """
    Check if any of the cases are resolved with type death and
    if so, mark the patient as deceased.  
    """
    from bhoma.apps.patient.models import CPatient
    patient = CPatient.get(patient_id)
    if not patient.is_deceased:
        for case in patient.cases:
            if case.outcome == Outcome.PATIENT_DIED:
                patient.handle_died()
                patient.save()
    else:
        save_pat = False
        for case in patient.cases:
            if not case.closed:
                case.manual_close(Outcome.PATIENT_DIED, datetime.utcnow())
                save_pat = True
        if save_pat:
            patient.save()

patient_updated.connect(update_patient_deceased_status)