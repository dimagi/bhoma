#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from couchdbkit.ext.django.schema import *
from datetime import datetime
import sys
import traceback
from couchversion.models import AppVersionedDocument

class ExceptionRecord(AppVersionedDocument):
    """
    A record of an exception
    """
    type = StringProperty()
    date = DateTimeProperty()
    message = StringProperty()
    stack_trace = StringProperty()
    url = StringProperty()
    query_params = DictProperty()
    archived = BooleanProperty(default=False)
    
    # super simple history tracking
    archived_by = StringProperty()
    archived_on = DateTimeProperty()
    reopened_by = StringProperty()
    reopened_on = DateTimeProperty()
    
    def get_status_display(self):
        if self.archived:
            return "archived%(on)s%(by)s" % \
                    {"by": " by %s" % self.archived_by if self.archived_by else "",
                     "on": " on %s" % self.archived_on if self.archived_on else ""}
        else:
            if self.reopened_by or self.reopened_on:
                return "reopened%(on)s%(by)s" % \
                    {"by": " by %s" % self.reopened_by if self.reopened_by else "",
                     "on": " on %s" % self.reopened_on if self.reopened_on else ""}
            else:
                return "open, never archived"
    
    def archive(self, by):
        self.archived = True
        self.archived_by = by
        self.archived_on = datetime.utcnow()
        self.save()
        
    def reopen(self, by):
        self.archived = False
        self.reopened_by = by
        self.reopened_on = datetime.utcnow()
        self.save()
        
    @classmethod
    def from_request_exception(cls, request):
        """
        Log an exceptional event (including request information
        that generated it)
        """
        url = request.build_absolute_uri()
        use_raw_data = False
        if request.method == "GET":
            query_params = request.GET
            url = url.split("?")[0]
        else:
            if request.META["CONTENT_TYPE"].startswith('text'):
                # if we have a text content type, just assume this
                # is a raw post we want to save as a file
                # and save that as an attachment
                use_raw_data = True
            query_params = {} if use_raw_data else request.POST
        type, exc, tb = sys.exc_info()
        traceback_string = "".join(traceback.format_tb(tb))
        record = ExceptionRecord(type=str(type),
                                 message=str(exc),
                                 stack_trace=traceback_string,
                                 date=datetime.utcnow(),
                                 url=url,
                                 query_params=query_params)
        record.save()
        if use_raw_data:
            record.put_attachment(request.raw_post_data, name="post_data", 
                                  content_type=request.META["CONTENT_TYPE"],
                                  content_length=len(request.raw_post_data))
        return record
    
    @classmethod
    def from_exc_info(cls, exc_info):
        """
        Log an exceptional event from the results of sys.exc_info()
        """
        type, exc, tb = exc_info
        traceback_string = "".join(traceback.format_tb(tb))
        record = ExceptionRecord(type=str(type),
                                 message=str(exc),
                                 stack_trace=traceback_string,
                                 date=datetime.utcnow(),
                                 url="",
                                 query_params={})
        record.save()
        return record        
        
import bhoma.apps.couchlog.signals