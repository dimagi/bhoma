from __future__ import absolute_import
from datetime import datetime, timedelta
from django.http import HttpRequest

import logging
from dimagi.utils.parsing import string_to_datetime
from django.utils.datetime_safe import strftime

FORMAT_STRING = "%b %Y"
class DateSpan(object):
    
    def __init__(self, startdate, enddate):
        self.startdate = startdate
        self.enddate = enddate
    
    @property
    def startdate_param(self, format=FORMAT_STRING):
        if self.startdate:
            return self.startdate.strftime(format)
    @property
    def enddate_param(self, format=FORMAT_STRING):
        if self.enddate:
            return self.enddate.strftime(format)
        
    
    def is_valid(self):
        # this is a bit backwards but keeps the logic in one place
        return not bool(self.get_validation_reason())
    
    def get_validation_reason(self):
        if self.startdate is None or self.enddate is None:
            return "You have to specify both dates!"
        else:
            if self.enddate < self.startdate:
                return "You can't have an end date of %s after start date of %s" % (self.enddate, self.startdate)
        return ""


def wrap_with_dates():
    """Wraps a request with dates based on url params or defaults and
       Checks date validity."""
    # this is loosely modeled after example number 4 of decorator
    # usage here: http://www.python.org/dev/peps/pep-0318/
    def get_dates(f):
        def wrapped_func(*args, **kwargs):
            # wrap everything besides the function call in a try/except
            # block.  we don't ever want this to prevent the 
            # basic view functionality from working. 
            # attempt to find the request object from all the argument
            # values, checking first the args and then the kwargs 
            req = None
            for arg in args:
                if _is_http_request(arg):
                    req = arg
                    break
            if not req:
                for arg in kwargs.values():
                    if _is_http_request(arg):
                        req = arg
                        break
            if req:
                dict = req.POST if req.method == "POST" else req.GET
                
                def date_or_nothing(param):
                    return datetime.strptime(dict[param], FORMAT_STRING)\
                             if param in dict and dict[param] else None
                
                startdate = date_or_nothing("startdate")
                enddate = date_or_nothing("enddate")
                
                if startdate or enddate:
                    req.dates = DateSpan(startdate, enddate)
                else:        
                    # default to the current month
                    now = datetime.now()
                    if now.month < 12:
                        first_of_next_month = datetime(now.year, now.month + 1, 1)
                    else:
                        first_of_next_month = datetime(now.year + 1, 1, 1)
                    enddate = first_of_next_month - timedelta(days=1)
                    startdate = datetime(now.year, now.month, 1)
                    req.dates = DateSpan(startdate, enddate)
                    
            return f(*args, **kwargs) 
        if hasattr(f, "func_name"):
            wrapped_func.func_name = f.func_name
            # preserve doc strings
            wrapped_func.__doc__ = f.__doc__  
            
            return wrapped_func
        else:
            # this means it wasn't actually a view.  
            return f 
    return get_dates

def _is_http_request(obj):
    return obj and isinstance(obj, HttpRequest)