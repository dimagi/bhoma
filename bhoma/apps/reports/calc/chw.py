from collections import defaultdict
from datetime import datetime
from dimagi.utils.couch.database import get_db

def get_monthly_case_breakdown(chw, startdate, enddate):
    startkey = [chw.current_clinic_id, chw.current_clinic_zone, startdate.year, startdate.month - 1]
    endkey = [chw.current_clinic_id, chw.current_clinic_zone, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_cases_by_month", group=True, group_level=4, 
                            startkey=startkey,endkey=endkey).all()
    
    ret = defaultdict(lambda: 0)
    for row in results:
        key_date = datetime(row["key"][2], row["key"][3] + 1, 1)
        ret[key_date] = row["value"]
    return ret
    
def get_monthly_referral_breakdown(chw, startdate, enddate):
    startkey = [chw.get_id, startdate.year, startdate.month - 1]
    endkey = [chw.get_id, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/chw_referral_ids",  
                            startkey=startkey,endkey=endkey).all()
    
    ids_and_dates = dict([(row["value"], datetime(row["key"][1], row["key"][2] + 1, 1)) for row in results])
    found = get_db().view("reports/chw_referrals_met",  
                          keys=ids_and_dates.keys(), group=True).all()
    
    ret = defaultdict(lambda: 0)
    for row in found:
        ret[ids_and_dates[row["key"]]] += 1
    
    return ret
    
