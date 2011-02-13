from bhoma.apps.patient.models import CPatient
from bhoma.const import VIEW_ALL_PATIENTS
from dimagi.utils.couch.database import get_db
from dimagi.utils import logging
from bhoma.apps.patient.processing import reprocess
from bhoma.apps.patient.conflicts import resolve_conflicts


def get_patient(patient_id):
    """
    Loads a patient from the database.  If any conflicts are detected this
    will run through all the xforms and regenerate the patient, deleting 
    all other revisions.
    """
    resolve_conflicts(patient_id)
    
    return CPatient.get(patient_id)