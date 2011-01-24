import calendar
from django.conf import settings
from bhoma.apps.case.models import CReferral
from bhoma.utils import render_to_response
from bhoma.utils.couch.database import get_db
from bhoma.apps.reports.decorators import wrap_with_dates
from bhoma.apps.xforms.util import get_xform_by_namespace, value_for_display
import bhoma.apps.xforms.views as xforms_views
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from bhoma.apps.reports.display import ReportDisplay, ReportDisplayRow,\
    NumericalDisplayValue
from bhoma.apps.patient.encounters.config import get_display_name
import itertools
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from bhoma.apps.chw.models.couch import CommunityHealthWorker
from couchdbkit.resource import ResourceNotFound
from bhoma.utils.parsing import string_to_datetime
from bhoma.apps.locations.models import Location
from bhoma.apps.reports.googlecharts import get_punchcard_url
from bhoma.apps.reports.calc.punchcard import get_data, get_clinics, get_users
from django.views.decorators.http import require_GET
from bhoma.apps.reports.templatetags.report_tags import render_user_inline,\
    render_report
from bhoma.apps.locations.util import clinic_display_name
from bhoma.apps.reports.calc import entrytimes
from bhoma.apps.reports.flot import get_sparkline_json, get_sparkline_extras,\
    get_cumulative_counts
from bhoma.apps.webapp.config import is_clinic
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions
from bhoma.apps.reports.calc.summary import get_clinic_summary
from bhoma.apps.reports.calc.mortailty import MortalityGroup
from django.utils.datastructures import SortedDict

def report_list(request):
    template = "reports/report_list_ts.html" if is_clinic() else "reports/report_list.html"
    return render_to_response(request, template, {"options": TouchscreenOptions.default()})

def clinic_summary(request, group_level=2):
    report = get_clinic_summary(group_level)
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
        date_row = get_db().view("reports/user_summary", 
                                 group=True, group_level=2, 
                                 endkey=[user_id], 
                                 startkey=[user_id, {}], 
                                 limit=1, descending=True).one()
        if date_row:
            row["last_submission_date"] = string_to_datetime(date_row["key"][1])
        
    return render_to_response(request, "reports/user_summary.html",
                              {"show_dates": False,
                               "results": results, 
                               "report": {"name": report_name}})
    

@require_GET
def entrytime(request):
    clinic_id = request.GET.get("clinic", None)
    user_id = request.GET.get("user", None)
    user_data = {}
    data = {}
    name = "Form Entry Time Report"
    if clinic_id:
        user_data = get_users(clinic_id)
        if user_id:
            selected_user = [user for user, _ in user_data if user["_id"] == user_id][0]
            name = "Form Entry Time Report for %s at %s" % (render_user_inline(selected_user), clinic_display_name(clinic_id)) 
        else:
            name = "Form Entry Time Report for %s (%s)" % (clinic_display_name(clinic_id), clinic_id)
    
    clinic_data = get_clinics()
    return render_to_response(request, "reports/entrytimes.html", 
                              {"report": {"name": name},
                               "chart_extras": get_sparkline_extras(data),
                               "clinic_data": clinic_data,
                               "user_data": user_data,
                               "clinic_id": clinic_id,
                               "user_id": user_id})


@require_GET
def single_chw_summary(request):
    chw_id = request.GET.get("chw", None)
    all_chws = get_db().view("phone/cases_sent_to_chws", group=True, group_level=1, reduce=True)
    chws = []
    main_chw = None
    for row in all_chws:
        chw = CommunityHealthWorker.get(row["key"][0])
        chws.append(chw)
        if chw_id == chw.get_id:
            main_chw = chw
        
    
    daily_case_data = []
    total_case_data = []
    punchcard_url = ""
    if main_chw:
        punchcard_url = get_punchcard_url(get_data(main_chw.current_clinic_id, chw_id), width=910)
        
    return render_to_response(request, "reports/chw_summary.html", 
                              {"report": {"name": "CHW summary%s" % \
                                          ("" if not main_chw else \
                                           " for %s (%s)" % (main_chw.formatted_name, main_chw.current_clinic_display))},
                               "chw_id": chw_id,
                               "main_chw":    main_chw,
                               "chws":   chws,
                               "punchcard_url":    punchcard_url,
                               })
                               


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
@wrap_with_dates()
def mortality_register(request):
    if not request.dates.is_valid():
        messages.error(request, request.dates.get_validation_reason())
        return render_to_response(request, "reports/mortality_register.html", 
                                  {"show_dates": True, "report": None})
    
    results = get_db().view("reports/nhc_cause_of_death", group=True, group_level=6, 
                            **_get_keys(request.dates.startdate, request.dates.enddate)).all()
        
    report_name = "NHC Register"
    clinic_map = {}
    # the structure of the above will be:
    # { clinic : { group: { type: count }}
    for row in results:
        # [2010,8,"5010","adult","f","heart_problem"]
        year, jsmonth, clinic, agegroup, gender, type_of_death = row["key"]
        count = row["value"]
        if not clinic in clinic_map:
            clinic_map[clinic] = {}
        group = MortalityGroup(clinic, agegroup, gender)
        if not group in clinic_map[clinic]:
            clinic_map[clinic][group] = []
        
        value_display = NumericalDisplayValue(count,type_of_death,hidden=False,
                                              display_name=value_for_display(type_of_death), 
                                              description="")
        clinic_map[clinic][group].append(value_display)
        
    all_clinic_rows = []
    for clinic, groups in clinic_map.items():
        try:
            clinic_obj = Location.objects.get(slug=clinic)
            clinic = "%s (%s)" % (clinic_obj.name, clinic_obj.slug)
        except Location.DoesNotExist:
            pass
        for group, rows in groups.items():
            keys = SortedDict()
            keys["clinic"] = clinic
            keys["age group"] =  group.agegroup
            keys["gender"] = group.gender
            all_clinic_rows.append(ReportDisplayRow(report_name, keys, rows))
                                                    
    report = ReportDisplay(report_name, all_clinic_rows)
    
    return render_to_response(request, "reports/mortality_register.html", 
                              {"show_dates": True, "report": report})
 
def enter_mortality_register(request):
    """
    Enter community mortality register from neighborhood health committee members
    """   
    def callback(xform, doc):
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


def clinic_summary_raw(request, group_level=2):
    report = get_clinic_summary(group_level)
    body = render_report(report, template="reports/text/couch_report_raw.txt")
    return HttpResponse(body, content_type="text/plain")
    


def _pi_report(request, view_name):
    """
    Generic report engine for the performance indicator reports
    """
    if not request.dates.is_valid():
        messages.error(request, request.dates.get_validation_reason())
        return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": True, "report": None})
                               
                                   
    
    
    results = get_db().view(view_name, group=True, group_level=3, 
                            **_get_keys(request.dates.startdate, request.dates.enddate)).all()
    report = ReportDisplay.from_pi_view_results(results)
    return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": True, "report": report})
    
def _get_keys(startdate, enddate):
    # set the start key to the first and the end key to the last of the month
    startkey = [startdate.year, startdate.month - 1]
    endkey = [enddate.year, enddate.month - 1, {}]
    return {"startkey": startkey, "endkey": endkey}