from bhoma.apps.couchlog.models import ExceptionRecord
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from bhoma.utils.logging import log_exception
from django.http import HttpResponse
from bhoma.utils.couch.database import get_db
from django.views.decorators.http import require_POST
import json


def dashboard(request):
    """
    View all couch error data
    """
    show = request.GET.get("show", "inbox")
    show_all = False
    if show == "all":
        show_all = True
    if show_all:
        errors = ExceptionRecord.view("couchlog/all_by_date")
    else:
        errors = ExceptionRecord.view("couchlog/inbox_by_date")
    return render_to_response('couchlog/dashboard.html',
                              {"show" : show, "logs": errors},
                               context_instance=RequestContext(request))

@require_POST
def update(request):
    """
    Update a couch log.
    """
    id = request.POST["id"]
    action = request.POST["action"]
    log = ExceptionRecord.get(id)
    if action == "archive":
        log.archived = True
        log.save()
        text = "archived! press to undo"
        next_action = "move_to_inbox"
    elif action == "move_to_inbox":
        log.archived = False
        log.save()
        text = "moved! press to undo"
        next_action = "archive"
    to_return = {"id": id, "text": text, "next_action": next_action,
                 "action": action, 
                 "style_class": "archived" if log.archived else "inbox"}
    return HttpResponse(json.dumps(to_return))
    