from bhoma.apps.patient.models import CPatient
from bhoma.apps.patient.conflicts import resolve_conflicts


def get_patient(patient_id):
    """
    Loads a patient from the database.  If any conflicts are detected this
    will run through all the xforms and regenerate the patient, deleting 
    all other revisions.
    """
    resolve_conflicts(patient_id)
    return CPatient.get(patient_id)