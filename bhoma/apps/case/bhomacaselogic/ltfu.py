from bhoma.apps.case import const
from datetime import datetime, time, timedelta
from bhoma.apps.case.models import PatientCase

def close_as_lost(case):
    """
    Closes a case as lost to follow up. The date closed will be the date lost,
    and the status will be lost.
    """
    # we should never be closing something as lost before the ltfu_date
    assert(case.ltfu_date <= datetime.utcnow().date())
    case.manual_close(const.Outcome.LOST_TO_FOLLOW_UP, 
                      datetime.combine(case.ltfu_date, time()))
    
def get_open_lost_cases(asof=None):
    """
    Given a date, return all open cases that should be marked lost
    as of that date. If no date is passed in, the current date 
    (in utc) will be used.
    """
    if asof is None:  asof = datetime.utcnow().date()
    cutoff = asof - timedelta(days=1)
    return PatientCase.view_with_patient("centralreports/open_ltfu_cases", 
                                         include_docs=True,
                                         startkey=cutoff.strftime("%Y-%m-%d"), 
                                         endkey="", descending=True)