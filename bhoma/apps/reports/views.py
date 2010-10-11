import calendar
from django.conf import settings
from bhoma.apps.case.models import CReferral
from bhoma.utils import render_to_response
from bhoma.utils.couch.database import get_db
from bhoma.apps.reports.decorators import wrap_with_dates
from bhoma.apps.xforms.util import get_xform_by_namespace
import bhoma.apps.xforms.views as xforms_views
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from bhoma.apps.reports.display import ReportDisplay, ReportDisplayRow,\
    NumericalDisplayValue
from bhoma.apps.patient.encounters.config import get_display_name
import itertools
from django.contrib.auth.decorators import permission_required
from bhoma.apps.chw.models.couch import CommunityHealthWorker
from couchdbkit.resource import ResourceNotFound
from bhoma.utils.parsing import string_to_datetime
from bhoma.apps.locations.models import Location
from bhoma.apps.reports.googlecharts import get_punchcard_url
from bhoma.apps.reports.calc.punchcard import get_data, get_clinics, get_users
from django.views.decorators.http import require_GET
from bhoma.apps.reports.templatetags.report_tags import render_user_inline
from bhoma.apps.locations.util import clinic_display_name
from bhoma.apps.reports.calc import entrytimes
from bhoma.apps.reports.flot import get_sparkline_json, get_sparkline_extras


def clinic_summary(request, group_level=2):
    results = get_db().view("xforms/counts_by_type", group=True, group_level=group_level).all() 
                            
    report_name = "Clinic Summary Report (number of forms filled in by type)"
    clinic_map = {}
    
    for row in results:
        key = row["key"]
        value = row["value"]
        namespace, clinic = key[:2]
        if not clinic in clinic_map:
            clinic_map[clinic] = []
        value_display = NumericalDisplayValue(value,namespace, hidden=False,
                                              display_name=get_display_name(namespace), description="")
        clinic_map[clinic].append(value_display)
    
    all_clinic_rows = []
    for clinic, rows in clinic_map.items():
        try:
            clinic_obj = Location.objects.get(slug=clinic)
            clinic = "%s (%s)" % (clinic_obj.name, clinic_obj.slug)
        except Location.DoesNotExist:
            pass
        all_clinic_rows.append(ReportDisplayRow(report_name, {"clinic": clinic},rows))
    report = ReportDisplay(report_name, all_clinic_rows)
    return render_to_response(request, "reports/couch_report.html",
                              {"show_dates": False, "report": report})
    

def user_summary(request):
    results = get_db().view("reports/user_summary", group=True, group_level=1).all() 
    report_name = "User Summary Report (number of forms filled in by person)"
    for row in results:
        # this is potentially 3N queries where N is the number of users.
        # could be slimmed down if it starts to be slow  
        user_id = row["key"][0]
        try:
            user = get_db().get(user_id)
        except Exception:
            user = None
        row["user"] = user
        # have to swap the start and end keys when you specify descending=true
        row["last_submission_date"] = string_to_datetime(get_db().view("reports/user_summary", 
                                                                       group=True, group_level=2, 
                                                                       endkey=[user_id], 
                                                                       startkey=[user_id, {}], 
                                                                       limit=1, descending=True).one()["key"][1])
        
    return render_to_response(request, "reports/user_summary.html",
                              {"show_dates": False,
                               "results": results, 
                               "report": {"name": report_name}})
    

@require_GET
def entrytime(request):
    # todo    
    clinic_id = request.GET.get("clinic", None)
    user_id = request.GET.get("user", None)
    url = None
    user_data = {}
    data = {}
    name = "Form Entry Time Report"
    if clinic_id:
        data = entrytimes.get_data(clinic_id, user_id)
        user_data = get_users(clinic_id)
        if user_id:
            selected_user = [user for user, _ in user_data if user["_id"] == user_id][0]
            name = "Form Entry Time Report for %s at %s" % (render_user_inline(selected_user), clinic_display_name(clinic_id)) 
        else:
            name = "Form Entry Time Report for %s (%s)" % (clinic_display_name(clinic_id), clinic_id)
    
    # url = get_sparkline_url({})
    clinic_data = get_clinics()
    return render_to_response(request, "reports/entrytimes.html", 
                              {"report": {"name": name},
                               "chart_data": get_sparkline_json(data), 
                               "chart_extras": get_sparkline_extras(data),
                               "clinic_data": clinic_data,
                               "user_data": user_data,
                               "clinic_id": clinic_id,
                               "user_id": user_id})


@require_GET
def punchcard(request):
    # todo    
    clinic_id = request.GET.get("clinic", None)
    user_id = request.GET.get("user", None)
    url = None
    user_data = {}
    name = "Punchcard Report"
    if clinic_id:
        url = get_punchcard_url(get_data(clinic_id, user_id))
        user_data = get_users(clinic_id)
        if user_id:
            selected_user = [user for user, _ in user_data if user["_id"] == user_id][0]
            name = "Punchcard Report for %s at %s" % (render_user_inline(selected_user), clinic_display_name(clinic_id)) 
        else:
            name = "Punchcard Report for %s (%s)" % (clinic_display_name(clinic_id), clinic_id)  
    clinic_data = get_clinics()
    return render_to_response(request, "reports/punchcard.html", 
                              {"report": {"name": name},
                               "chart_url": url, 
                               "clinic_data": clinic_data,
                               "user_data": user_data,
                               "clinic_id": clinic_id,
                               "user_id": user_id})

def unrecorded_referral_list(request):
    """
    Clinic able to pull up list of Open Cases that require bookkeeping.
    Any open case without a follow-up either at the clinic or from the 
    CHW after 6 weeks is given the Outcome: 'Lost Follow Up.' The report 
    also lists cases closed by the CHW and their outcome for the CSW to 
    record in the patient folder.
    """
    # display list of open cases but unrecorded cases (referrals)
    referrals = CReferral.view("reports/closed_unrecorded_referrals")
    return render_to_response(request, "reports/closed_unrecorded_referrals.html",
                              {"show_dates": True, "referrals": referrals})
 
def mortality_register(request):
    """
    Enter community mortality register from neighborhood health committee members
    """   
    def callback(xform, doc):
        # TODO: add callback
        return HttpResponseRedirect(reverse("report_list"))  
    
    
    xform = get_xform_by_namespace("http://cidrz.org/bhoma/mortality_register")
    # TODO: generalize this better
    preloader_data = {"meta": {"clinic_id": settings.BHOMA_CLINIC_ID,
                               "user_id":   request.user.get_profile()._id,
                               "username":  request.user.username}}
    return xforms_views.play(request, xform.id, callback, preloader_data)

@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def under_five_pi(request):
    """
    Under five performance indicator report
    """
    return _pi_report(request, "reports/under_5_pi")
        
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def adult_pi(request):
    """
    Adult performance indicator report
    """
    return _pi_report(request, "reports/adult_pi")

    
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def pregnancy_pi(request):
    """
    Pregnancy performance indicator report
    """
    return _pi_report(request, "reports/pregnancy_pi")
        
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def chw_pi(request):
    """
    CHW performance indicator report
    """
    return _pi_report(request, "reports/chw_pi")

def _pi_report(request, view_name):
    """
    Generic report engine for the performance indicator reports
    """
    results = get_db().view(view_name, group=True, group_level=3, 
                            **_get_keys(request.startdate, request.enddate)).all()
    report = ReportDisplay.from_pi_view_results(results)
    return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": True, "report": report})
    
def _get_keys(startdate, enddate):
    # set the start key to the first and the end key to the last of the month
    startkey = [startdate.year, startdate.month - 1]
    endkey = [enddate.year, enddate.month - 1, {}]
    return {"startkey": startkey, "endkey": endkey}