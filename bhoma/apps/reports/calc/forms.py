from datetime import timedelta
from dimagi.utils.couch.database import get_db

def forms_submitted(user_id, xmlns, startdate, enddate):
    enddate = enddate + timedelta(days=1)
    startkey = ["utd", user_id, xmlns, startdate.year, 
                startdate.month - 1, startdate.day]
    endkey = ["utd", user_id, xmlns, enddate.year, 
              enddate.month - 1, enddate.day]
    ret = get_db().view("centralreports/chw_submission_counts", 
                        startkey=startkey, endkey=endkey, reduce=True).one()
    return ret["value"] if ret else 0
    