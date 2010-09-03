from bhoma.apps.patient.models import CPatient
from bhoma.const import VIEW_ALL_PATIENTS
from bhoma.utils.couch.database import get_db
from bhoma.utils import logging
from bhoma.apps.patient.processing import reprocess


def get_patient(patient_id):
    """
    Loads a patient from the database.  If any conflicts are detected this
    will run through all the xforms and regenerate the patient, deleting 
    all other revisions.
    """
    
    def resolve_conflicts(pat_id, conflicts):
        # For now conflict resolution assumes that all you ever need 
        # to do is reprocess the patient and delete the conflicts.
        reprocess(pat_id)
        conflict_docs = [get_db().get(pat_id, rev=conflict) for conflict in conflicts]
        get_db().bulk_delete(conflict_docs)
        
    pat_data = get_db().get(patient_id, conflicts=True)
    
    if "_conflicts" in pat_data:
        tries = 0
        while tries < 5:
            try:
                resolve_conflicts(patient_id, pat_data["_conflicts"])
                break
            except Exception, e:
                logging.log_exception(e)
                tries = tries + 1
     
    return CPatient.get(patient_id)