from bhoma.apps.patient.models import CPatient
from bhoma.const import VIEW_ALL_PATIENTS


def get_patient(patient_id):
    """
    Loads a patient from the database.  If any conflicts are detected this
    will run through all the xforms and regenerate the patient, deleting 
    all other revisions.
    """
    patient = CPatient.view(VIEW_ALL_PATIENTS, key=patient_id).one()
    return patient