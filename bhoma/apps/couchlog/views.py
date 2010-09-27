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
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from bhoma.apps.djangocouch.utils import futon_url
from django.utils.text import truncate_words
from bhoma.apps.locations.models import Location
from bhoma.utils.couch.pagination import CouchPaginator

def dashboard(request):
    """
    View all couch error data
    """
    show = request.GET.get("show", "inbox")
    return render_to_response('couchlog/dashboard.html',
                              {"show" : show, "count": True,
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

def paging(request):
    
    # what to show
    query = request.POST if request.method == "POST" else request.GET
    show = query.get("show", "inbox")
    show_all = False
    if show == "all":
        show_all = True
    
    view_name = "couchlog/all_by_date" if show_all else "couchlog/inbox_by_date"
    
    def wrapper_func(row):
        """
        Given a row of the view, get out an exception record
        """
        error = ExceptionRecord.wrap(row["value"])
        return [error.get_id,
                error.archived, 
                getattr(error, "clinic_id", "UNKNOWN"), 
                error.date.strftime('%Y-%m-%d %H:%M:%S') if error.date else "", 
                error.type, 
                error.message, 
                error.url,
                "archive",
                "email"]
    
    paginator = CouchPaginator(view_name, wrapper_func, search=False)
    
    # get our previous start/end keys if necessary
    # NOTE: we don't actually do anything with these yet, but we should for 
    # better pagination down the road.  using the "skip" parameter is not
    # super efficient.
    startkey = query.get("startkey", None)
    if startkey:
        startkey = json.loads(startkey)
    endkey = query.get("endkey", None)
    if endkey:
        endkey = json.loads(endkey)
    
    total_records = get_db().view("couchlog/count").one()["value"]
    
    return paginator.get_ajax_response(request, extras={"startkey": startkey,
                                                        "endkey": endkey,
                                                        "iTotalRecords": total_records})
                                    
        


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
    to = request.POST["to"].split(",")
    notes = request.POST["notes"]
    log = ExceptionRecord.get(id)
    if request.user and not request.user.is_anonymous():
        name = request.user.get_full_name()
        username = request.user.username
        reply_to = "%s <%s>" % (request.user.get_full_name(), request.user.email)
    else:
        name = ""
        username = "unknown"
        reply_to = settings.EMAIL_HOST_USER
    email_body = render_to_string("couchlog/email.txt",
                                  {"user_info": "%s (%s)" % (name, username),
                                   "notes": notes,
                                   "exception_url": futon_url(id)})
    
    try:
        email = EmailMessage("[BHOMA ERROR] %s" % truncate_words(log.message, 10), 
                             email_body, name,
                             to, 
                             headers = {'Reply-To': reply_to})
        email.send(fail_silently=False)
        return HttpResponse(json.dumps({"id": id,
                                        "success": True}))
    except Exception, e:
        log_exception()
        return HttpResponse(json.dumps({"id": id,
                                        "success": False, 
                                        "message": str(e)}))