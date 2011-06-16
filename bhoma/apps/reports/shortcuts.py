'''
Shortcuts for report queries
'''
from collections import defaultdict
from datetime import datetime
from dimagi.utils.couch.database import get_db
from dimagi.utils.parsing import string_to_datetime
from bhoma.apps.xforms.models.couch import CXFormInstance

def get_last_submission_date(user_id):
    # have to swap the start and end keys when you specify descending=true
    date_row = get_db().view("reports/user_submission_dates", 
                                 group=True, group_level=2,
                                 endkey=[user_id], 
                                 startkey=[user_id, {}], 
                                 limit=1, descending=True).one()
    if date_row:
        return string_to_datetime(date_row["key"][1])

def get_first_submission_date(user_id):
    date_row = get_db().view("reports/user_submission_dates", 
                                 group=True, group_level=2,
                                 startkey=[user_id], 
                                 endkey=[user_id, {}], 
                                 limit=1).one()
    if date_row:
        return string_to_datetime(date_row["key"][1])

def get_forms_submitted(user_id):
    results = get_db().view("reports/user_summary", group=True, group_level=1, 
                            startkey=[user_id],endkey=[user_id, {}],  
                            limit=1).one()
    if results:
        return results["value"]
    return 0

def get_submission_breakdown(user_id):
    results = get_db().view("reports/user_summary", group=True, group_level=2, 
                            startkey=[user_id],endkey=[user_id, {}]).all()
    ret = defaultdict(lambda: 0)
    for row in results:
        ret[row["key"][1]] = row["value"]
    return ret

def get_monthly_submission_breakdown(user_id, xmlns, startdate, enddate):
    
    startkey = [user_id, xmlns, startdate.year, startdate.month - 1]
    endkey = [user_id, xmlns, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/user_summary", group=True, group_level=4, 
                            startkey=startkey,endkey=endkey).all()
    ret = defaultdict(lambda: 0)
    for row in results:
        key_date = datetime(row["key"][2], row["key"][3] + 1, 1)
        ret[key_date] = row["value"]
    return ret

def get_recent_forms(user_id, xmlns, limit=3):
    """
    Get the N (limit) most recently submitted forms by a user of a certain
    type.
    """
    results = get_db().view("reports/user_summary", reduce=False, descending=True,
                            endkey=[user_id, xmlns],startkey=[user_id, xmlns, {}],  
                            include_docs=True, limit=limit).all()
    ret = []
    for row in results:
        ret.append(CXFormInstance.wrap(row["doc"]))
        
    return ret

def get_forms_in_window(user_id, xmlns, startdate, enddate):
    """
    Get all forms submitted by a user that fall between two dates.
    This is only available on the granularity of months.
    """
    startkey = [user_id, xmlns, startdate.year, startdate.month - 1]
    endkey = [user_id, xmlns, enddate.year, enddate.month - 1, {}]
    results = get_db().view("reports/user_summary", reduce=False, 
                            startkey=startkey,endkey=endkey).all()
    return [row["id"] for row in results]
        