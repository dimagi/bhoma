from datetime import datetime
from bhoma.apps.couchlog.models import ExceptionRecord
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from bhoma.utils.logging import log_exception
from django.http import HttpResponse
from bhoma.utils.couch.database import get_db
from django.views.decorators.http import require_POST
import json
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from bhoma.apps.djangocouch.utils import futon_url
from django.utils.text import truncate_words
from bhoma.apps.locations.models import Location

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
                              {"show" : show, "logs": errors, 
                               "support_email": settings.BHOMA_SUPPORT_EMAIL },
                               context_instance=RequestContext(request))

def single(request, log_id):
    log = ExceptionRecord.get(log_id)
    # monkeypatch the clinic name on
    if getattr(log, "clinic_id", ""):
        try:
            log.clinic_name = Location.objects.get(slug=log.clinic_id).name
        except Location.DoesNotExist:
            pass
    return render_to_response("couchlog/ajax/single.html", 
                              {"log": log},
                              context_instance=RequestContext(request))

@require_POST
def update(request):
    """
    Update a couch log.
    """
    id = request.POST["id"]
    action = request.POST["action"]
    if not id:
        raise Exception("no id!")
    log = ExceptionRecord.get(id)
    username = request.user.username if request.user and not request.user.is_anonymous() else "unknown"
    if action == "archive":
        log.archived = True
        log.archived_by = username
        log.archived_on = datetime.utcnow()
        log.save()
        text = "archived! press to undo"
        next_action = "move_to_inbox"
    elif action == "move_to_inbox":
        log.archived = False
        log.reopened_by = username
        log.reopened_on = datetime.utcnow()
        log.save()
        text = "moved! press to undo"
        next_action = "archive"
    to_return = {"id": id, "text": text, "next_action": next_action,
                 "action": action, 
                 "style_class": "archived" if log.archived else "inbox"}
    return HttpResponse(json.dumps(to_return))
    
@require_POST
def email(request):
    """
    Update a couch log.
    """
    id = request.POST["id"]
    to = request.POST["to"]
    notes = request.POST["notes"]
    log = ExceptionRecord.get(id)
    email_body = render_to_string("couchlog/email.txt",
                                  {"username": request.user.username if request.user and not request.user.is_anonymous() else "unknown",
                                   "notes": notes,
                                   "exception_url": futon_url(id)})
    
    try:
        send_mail("[BHOMA ERROR] %s" % truncate_words(log.message, 10), 
                  email_body, settings.EMAIL_HOST_USER,
                  [to], fail_silently=False)
        return HttpResponse(json.dumps({"id": id,
                                        "success": True}))
    except Exception, e:
        log_exception()
        return HttpResponse(json.dumps({"id": id,
                                        "success": False, 
                                        "message": str(e)}))