#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from couchdbkit.ext.django.schema import *
from datetime import datetime
import json
import sys
import traceback

class ExceptionRecord(Document):
    """
    A record of an exception
    """
    type = StringProperty()
    date = DateTimeProperty()
    message = StringProperty()
    stack_trace = StringProperty()
    url = StringProperty()
    query_params = DictProperty()
    
    @classmethod
    def from_request_exception(cls, request):
        """
        Log an exceptional event (optionally including request information
        that generated it)
        """
        url = request.build_absolute_uri()
        if request.method == "GET":
            query_params = request.GET
        else:
            query_params = request.POST
        
        type, exc, tb = sys.exc_info()
        traceback_string = '\n'.join(traceback.format_tb(tb))
        record = ExceptionRecord(type=str(type),
                                 message=str(exc),
                                 stack_trace=traceback_string,
                                 date=datetime.utcnow(),
                                 url=url,
                                 query_params=query_params)
        record.save()
        return record

import bhoma.apps.couchlog.signals