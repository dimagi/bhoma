from bhoma.apps.couchlog.models import ExceptionRecord
from django.shortcuts import render_to_response
from django.template.context import RequestContext


def dashboard(request):
    """
    View all couch error data
    """
    errors = ExceptionRecord.view("couchlog/by_date").all()
    return render_to_response('couchlog/dashboard.html',
                              {"logs": errors},
                               context_instance=RequestContext(request))
