from bhoma.apps.patient.processing import reprocess
from dimagi.utils.couch.database import get_db
from dimagi.utils.logging import log_exception
import logging

def resolve_conflicts(patient_id):
    """
    Resolve conflicts on a patient.  Returns true if conflicts were
    found, otherwise false. 
    """
    pat_data = get_db().get(patient_id, conflicts=True)
    
    if "_conflicts" in pat_data:
        tries = 0
        while tries < 5:
            try:
                # For now conflict resolution assumes that all you ever need 
                # to do is reprocess the patient and delete the conflicts.
                reprocess(patient_id)
                conflict_docs = [get_db().get(patient_id, rev=conflict) for conflict in pat_data["_conflicts"]]
                get_db().bulk_delete(conflict_docs)
                return True
            except Exception, e:
                log_exception(e)
                tries = tries + 1
        logging.error("Couldn't resolve conflicts for document %s" % patient_id)
        return True
    
    return False