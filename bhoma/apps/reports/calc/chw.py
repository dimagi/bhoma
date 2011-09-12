from collections import defaultdict
from datetime import datetime, time
from dimagi.utils.couch.database import get_db
from bhoma.apps.patient.models import CPatient
from bhoma.apps.case.models import PatientCase
from dimagi.utils.parsing import string_to_datetime
from bhoma.apps.case.models.couch import CommCareCase

def get_monthly_case_breakdown(chw, startdate, enddate):
    """
    Gets CommCareCase objects assigned to the CHW that were due in a given 
    month. 
    
    Returns a dictionary mapping dates to the number of cases from that month.
    """
    startkey = [chw.current_clinic_id, chw.current_clinic_zone, startdate.year, startdate.month - 1]
    endkey = [chw.current_clinic_id, chw.current_clinic_zone, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_cases_by_month", group=True, group_level=4, 
                            startkey=startkey,endkey=endkey).all()
    
    ret = defaultdict(lambda: 0)
    for row in results:
        key_date = datetime(row["key"][2], row["key"][3] + 1, 1)
        ret[key_date] = row["value"]
    return ret

def get_monthly_case_list(chw, startdate, enddate):
    """
    Like get_monthly_case_breakdown but return lists of the actual CommCareCase
    objects.
    
    A case is included in the date range based on the first date the case 
    is synced to the phone.
    """
    
    data = get_db().view("phone/cases_sent_to_chws", group=True, group_level=2, reduce=True, 
                         startkey=[chw.get_id], endkey=[chw.get_id, {}])

    monthly_breakdown = defaultdict(lambda: [])
    for row in data:
        case_id = row["key"][1]
        first_synced = string_to_datetime(row["value"])
        first_synced = datetime(first_synced.year, first_synced.month, first_synced.day)
        if startdate <= first_synced and first_synced < enddate:
            monthly_breakdown[datetime(first_synced.year, first_synced.month, first_synced.day)]\
                                .append(case_id)
        
    return monthly_breakdown
    
    
def get_referrals_made(chw, startdate, enddate):
    startkey = [chw.get_id, startdate.year, startdate.month - 1]
    endkey = [chw.get_id, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_referral_ids",  
                            startkey=startkey,endkey=endkey,
                            reduce=False).all()
    
    # maps referral ids to dates (months)
    return dict([(row["value"], datetime(row["key"][1], row["key"][2] + 1, 1)) for row in results])
    
def get_referrals_found(referrals):
    """
    Given a list of referrals, return the ones which are found in a clinic form
    """
    return [row["key"] for row in \
            get_db().view("reports/chw_referrals_met",  
                          keys=referrals, group=True).all()]
    
def get_monthly_referral_breakdown(chw, startdate, enddate):
    """
    Gets a dict of dates (months) mapping to the number of referrals
    made by a chw in that month that eventually turned up at the clinic
    
    returns a structure like
    { date: {made: 5, found: 4}}
    """
    ids_and_dates = get_referrals_made(chw, startdate, enddate)
    found = get_referrals_found(ids_and_dates.keys())
    ret = defaultdict(lambda: defaultdict(lambda: 0))
    # maps dates (months) to counts of found referrals
    for ref in ids_and_dates:
        ret[ids_and_dates[ref]]["made"] += 1
        if ref in found:
            ret[ids_and_dates[ref]]["found"] += 1
    return ret
    
def get_monthly_fu_breakdown(chw, startdate, enddate):
    """
    Emit a list of followup forms filled in by the CHW in a given period
    broken down by whether they closed the case and what the outcome was.
    
    Returns a dict with the following structure:
    
    {date(month): {closes?(true/false): {outcome: count}}}
    """
    startkey = [chw.get_id, startdate.year, startdate.month - 1]
    endkey = [chw.get_id, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_fu_breakdown", group=True, group_level=5, 
                            startkey=startkey,endkey=endkey).all()
    
    ret = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
    # sample: {date: {closes?(true/false): {outcome: count}}}
    for row in results:
        key_date = datetime(row["key"][1], row["key"][2] + 1, 1)
        closes_case = bool(row["key"][3])
        outcome = row["key"][4]
        ret[key_date][closes_case][outcome] = row["value"]
    return ret
    
def get_monthly_danger_sign_referred_breakdown(chw, startdate, enddate):
    startkey = [chw.get_id, startdate.year, startdate.month - 1] 
    endkey = [chw.get_id, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_pi", group=True, group_level=4, 
                            startkey=startkey,endkey=endkey).all()
    # sample: {date: [<danger_signs && referred count>, <danger_signs count>]}
    return dict([(datetime(row["key"][1], row["key"][2] + 1, 1), row["value"]) for row in results])

def followup_made(case_id):
    """
    For a given case id, return if a followup was made against it
    """
    # NOTE: Due to the way the system works the only time a case has more
    # than one form submitted against it is when a CHW makes a follow up.
    # Clinic forms _only_ create new case or _manually close_ existing cases
    # (not with a form). Therefore a proxy for this logic is that the case
    # has 2 or more forms submitted against it.
    return get_db().view("case/xform_case", key=case_id).one()["value"] > 1
    
    
def successful_followup_made(casedoc):
    return "bhoma_close" in casedoc and casedoc.bhoma_close \
           and casedoc.bhoma_outcome != "lost_to_followup_time_window"