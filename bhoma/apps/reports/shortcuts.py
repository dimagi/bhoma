'''
Shortcuts for report queries
'''
from bhoma.utils.couch.database import get_db
from bhoma.utils.parsing import string_to_datetime
from collections import defaultdict

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