from collections import defaultdict
from datetime import datetime, time
from dimagi.utils.couch.database import get_db
from bhoma.apps.patient.models import CPatient

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
    """
    startkey = [chw.current_clinic_id, chw.current_clinic_zone, startdate.year, startdate.month - 1]
    endkey = [chw.current_clinic_id, chw.current_clinic_zone, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_cases_by_month", startkey=startkey,endkey=endkey,
                            reduce=False).all()
    
    ret = []
    for pat_id in set((row["id"] for row in results)):
        pat = CPatient.get(pat_id)
        for case in pat.cases:
            for cc_case in case.commcare_cases:
                if startdate <= datetime.combine(cc_case.due_date, time()) <= enddate:
                    #print "%s, %s" % (pat.get_id, cc_case.get_id)
                    ret.append(cc_case)
    return ret
    
    
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
    