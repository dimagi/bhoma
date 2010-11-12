from datetime import date, datetime, timedelta, time
from bhoma.utils.logging import log_exception

def force_to_date(date_or_datetime):
    """Forces a date or datetime to a date."""
    if not date_or_datetime:                   return date_or_datetime
    if isinstance(date_or_datetime, datetime): return date_or_datetime.date()
    if isinstance(date_or_datetime, date):     return date_or_datetime
    else:                                      raise ValueError("object must be date or datetime!")
    
def force_to_datetime(date_or_datetime):
    """Forces a date or datetime to a datetime."""
    if not date_or_datetime:                    return date_or_datetime
    if isinstance(date_or_datetime, datetime):  return date_or_datetime
    elif isinstance(date_or_datetime, date):    return datetime.combine(date, time())
    else:                                       raise ValueError("object must be date or datetime!")    
        
def safe_date_add(startdate, days, force_to_date_flag=True):
    if not startdate:  return None
    try: 
        val = startdate + timedelta(days)
        if force_to_date_flag:  return force_to_date(val)
        else:                   return val 
    except OverflowError, e:
        log_exception(e) 
        return None

