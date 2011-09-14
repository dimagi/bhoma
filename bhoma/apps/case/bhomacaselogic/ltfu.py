from bhoma.apps.case import const
from datetime import datetime, time

def close_as_lost(case):
    """
    Closes a case as lost to follow up. The date closed will be the date lost,
    and the status will be lost.
    """
    # we should never be closing something as lost before the ltfu_date
    assert(case.ltfu_date <= datetime.utcnow().date())
    case.manual_close(const.Outcome.LOST_TO_FOLLOW_UP, 
                      datetime.combine(case.ltfu_date, time()))