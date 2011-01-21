"""
Logic about chws phones and cases go here.
"""
from django.core.cache import cache
from bhoma.apps.case.models.couch import PatientCase
from couchdbkit.consumer import Consumer
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.models import CPatient
from bhoma.apps.phone.models import PhoneCase
import logging

def get_pats_with_updated_cases(clinic_id, zone, last_seq):
    """
    Given a clinic, zone, and last_seq id from couch, get the patients whose
    cases have been updated, returning a tuple of updated ids (in a list) and
    the last seq number.
    """
    CACHE_TIME = 4 * 60 * 60 # cache for 4 hours, in seconds
    
    # first try to get this from the cache
    def _build_cache_key(clinic_id, zone, last_seq):
        return "sync_patient_list:%s:%s:%s" % (clinic_id, zone, last_seq)
    cached_data = cache.get(_build_cache_key(clinic_id, zone, last_seq))
    if cached_data:
        return cached_data
    
    # first get the patient list of potential matches.  use the open case
    # list to get patient ids
    potential_case_list = get_db().view("case/open_for_chw_for_phone", key=[clinic_id, zone])
    possible_pat_ids = []
    for row in potential_case_list:
        if row["id"] not in possible_pat_ids:
            possible_pat_ids.append(row["id"])
    # new consumer
    consumer = Consumer(get_db())
    view_results = consumer.fetch(since=last_seq)
    pats_with_open_cases = []
    for res in view_results["results"]:
        id = res["id"]
        if id in possible_pat_ids and not id in pats_with_open_cases:
            pats_with_open_cases.append(id)
    
    updated_last_seq = view_results["last_seq"]
    ret = (pats_with_open_cases, updated_last_seq)
    cache.set(_build_cache_key(clinic_id, zone, last_seq), ret, CACHE_TIME)
    return ret

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
    case_ids = []
    for id in patient_ids:
        pat = CPatient.get(id)
        for case in pat.cases:
            if not case.closed and case.send_to_phone and case.get_id not in case_ids:
                case.patient = pat
                phone_case = PhoneCase.from_bhoma_case(case)
                if phone_case and phone_case.is_started():
                    # keep a running list of case ids sent down because the phone doesn't
                    # deal well with duplicates.  There shouldn't be duplicates, but they
                    # can come up with bugs, so arbitrarily only send down the first case
                    # if there are any duplicates
                    if phone_case.case_id in case_ids:
                        logging.error("Found a duplicate case for %s. Will not be sent to phone." % phone_case.case_id)
                    else:
                        case_ids.append(phone_case.case_id)
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
