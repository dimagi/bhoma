"""
Logic about chws phones and cases go here.
"""
from bhoma.apps.case.models.couch import PatientCase
from couchdbkit.consumer import Consumer
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.models import CPatient

def meets_sending_criteria(case, synclog):
    """
    Whether this case should be sent out.
    """
    # if never before synced, always include this
    if not synclog: return True
    # otherwise only sync something that's been modified since the date of the log
    return case.modified_on > synclog.date
    
def get_pats_with_updated_cases(clinic_id, zone, last_seq):
    """
    Given a clinic, zone, and last_seq id from couch, get the patients whose
    cases have been updated, returning a tuple of updated ids (in a list) and
    the last seq number.
    """
    consumer = Consumer(get_db())
    view_results = consumer.fetch(filter="case/patients_in_zone_with_open_cases", 
                                  clinic_id=clinic_id, zone=zone,
                                  since=last_seq)
    
    pats_with_open_cases = list(set([res["id"] for res in view_results["results"]]))
    updated_last_seq = view_results["last_seq"]
    return (pats_with_open_cases, updated_last_seq)
    
def get_open_cases_to_send(patient_ids, last_sync):
    """
    Given a list of patients, get the open/updated cases since the last sync
    operation
    """
    for id in patient_ids:
        pat = CPatient.get(id)
        for case in pat.cases:
            if not case.closed:
                case.patient = pat
                yield case
    
def cases_for_chw(chw):
    """
    From chw clinic zone, get the list of open cases
    """
    key = [chw.current_clinic_id, chw.current_clinic_zone]
    return PatientCase.view_with_patient("case/open_for_chw", key=key).all()

def cases_for_patient(patient_id):
    """
    Get the list of open cases for a particular patient
    """
    return PatientCase.view_with_patient("case/open_for_patient", key=patient_id).all()
