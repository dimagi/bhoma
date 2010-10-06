"""
Logic about chws phones and cases go here.
"""
from bhoma.apps.case.models.couch import PatientCase
from couchdbkit.consumer import Consumer
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.models import CPatient
from bhoma.apps.phone.models import PhoneCase

def get_pats_with_updated_cases(clinic_id, zone, last_seq):
    """
    Given a clinic, zone, and last_seq id from couch, get the patients whose
    cases have been updated, returning a tuple of updated ids (in a list) and
    the last seq number.
    """
    consumer = Consumer(get_db())
    view_results = consumer.fetch(filter="case/patients_in_zone_with_open_cases_for_phones", 
                                  clinic_id=clinic_id, zone=zone,
                                  since=last_seq)
    
    pats_with_open_cases = list(set([res["id"] for res in view_results["results"]]))
    updated_last_seq = view_results["last_seq"]
    return (pats_with_open_cases, updated_last_seq)

def case_previously_synced(case_id, last_sync):
    if not last_sync: return False
    return case_id in last_sync.get_synced_case_ids()
    
    
def get_open_cases_to_send(patient_ids, last_sync):
    """
    Given a list of patients, get the open/updated cases since the last sync
    operation.  This returns tuples phone_case objects, and flags that say 
    whether or not they should be created
    """ 
    to_return = []
    for id in patient_ids:
        pat = CPatient.get(id)
        for case in pat.cases:
            if not case.closed and case.send_to_phone:
                case.patient = pat
                phone_case = PhoneCase.from_bhoma_case(case)
                if phone_case and phone_case.is_started():
                    # HACK: TODO: don't send down pregnancy cases yet.
                    if phone_case.followup_type != "pregnancy":
                        previously_synced = case_previously_synced(phone_case.case_id, last_sync)
                        to_return.append((phone_case, not previously_synced))
    return to_return
    
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
