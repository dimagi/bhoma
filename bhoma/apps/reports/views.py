from django.conf import settings
from bhoma.apps.case.models import CReferral
from dimagi.utils.web import render_to_response
from dimagi.utils.couch.database import get_db
from dimagi.utils.parsing import string_to_datetime
from dimagi.utils.dates import add_months
from bhoma.apps.reports.decorators import wrap_with_dates
from bhoma.apps.xforms.util import get_xform_by_namespace, value_for_display
from collections import defaultdict
import bhoma.apps.xforms.views as xforms_views
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, resolve
from bhoma.apps.reports.display import ReportDisplay, ReportDisplayRow,\
    NumericalDisplayValue
from bhoma.apps.patient.encounters.config import get_display_name
import itertools
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from bhoma.apps.chw.models import CommunityHealthWorker
from couchdbkit.resource import ResourceNotFound
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
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions
from bhoma.apps.webapp.models import Ping
from bhoma.apps.reports.calc.summary import get_clinic_summary
from bhoma.apps.reports.calc.mortailty import MortalityGroup, MortalityReport,\
    CauseOfDeathDisplay, AGGREGATE_OPTIONS
from django.utils.datastructures import SortedDict
from datetime import datetime, timedelta
from bhoma.apps.reports.shortcuts import get_last_submission_date,\
    get_first_submission_date, get_forms_submitted, get_submission_breakdown,\
    get_recent_forms, get_monthly_submission_breakdown
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.calc.pi import get_chw_pi_report
from bhoma.scripts.reversessh_tally import parse_logfile, tally, TAGS

def report_list(request):
    template = "reports/report_list_ts.html" if is_clinic() else "reports/report_list.html"
    return render_to_response(request, template, {"options": TouchscreenOptions.default()})

def clinic_summary(request, group_level=2):
    """Clinic Summary Report"""
    report = get_clinic_summary(group_level)
    return render_to_response(request, "reports/couch_report.html",
                              {"show_dates": False, "report": report})
    
def user_summary(request):
    """User and CHW Summary Report (# forms/person)"""
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
        row["last_submission_date"] = get_last_submission_date(user_id)
        
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
@wrap_with_dates()
def single_chw_summary(request):
    chw_id = request.GET.get("chw", None)
    chws = CommunityHealthWorker.view("chw/by_clinic", include_docs=True)
    main_chw = CommunityHealthWorker.get(chw_id) if chw_id else None
    
    punchcard_url = ""
    if main_chw:
        punchcard_url = get_punchcard_url(get_data(main_chw.current_clinic_id, chw_id), width=910)
        # patch on extra data for display
        main_chw.last_submission = get_last_submission_date(main_chw.get_id)    
        main_chw.first_submission = get_first_submission_date(main_chw.get_id)    
        main_chw.forms_submitted = get_forms_submitted(main_chw.get_id)    
        forms_breakdown = get_submission_breakdown(main_chw.get_id)
        main_chw.hh_surveys = forms_breakdown[config.CHW_HOUSEHOLD_SURVEY_NAMESPACE]
        main_chw.fus = forms_breakdown[config.CHW_FOLLOWUP_NAMESPACE]
        main_chw.refs = forms_breakdown[config.CHW_REFERRAL_NAMESPACE]
        main_chw.monthly_surveys = forms_breakdown[config.CHW_MONTHLY_SURVEY_NAMESPACE]
        
        # recent monthly surveys
        main_chw.recent_surveys = get_recent_forms(main_chw.get_id, config.CHW_MONTHLY_SURVEY_NAMESPACE)
        
        if not request.dates.is_valid():
            messages.error(request, request.dates.get_validation_reason())
            messages.warning(request, "Performance Indicators are not displayed. Please fix the other errors")
            report = {"name": "Partial CHW Summary for %s" % main_chw.formatted_name}
        else:
            report = get_chw_pi_report(main_chw, request.dates.startdate, request.dates.enddate)
    else:        
        report = {"name": "CHW Summary"}
    fake_hh_data = []
    now = datetime.now()
    for i in range(3):
        year, month = add_months(now.year, now.month, -i)
        fake_hh_data.append(["%s %s" % (year, month), 100, 200, "25%", "13%"])
        
    return render_to_response(request, "reports/chw_summary.html", 
                              {"report": report,
                               "chw_id": chw_id,
                               "main_chw":    main_chw,
                               "chws":   chws,
                               "punchcard_url":    punchcard_url,
                               "show_dates": False,
                               "hh_data": fake_hh_data, # TODO
                               "fu_data": fake_hh_data, # TODO
                               "ref_data": fake_hh_data # TODO
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
    
    clinic_id = request.GET.get("clinic", None)
    main_clinic = Location.objects.get(slug=clinic_id) if clinic_id else None
    cause_of_death_report = MortalityReport()
    place_of_death_report = MortalityReport()
    global_map = defaultdict(lambda: 0)
    global_display = CauseOfDeathDisplay("Total", AGGREGATE_OPTIONS)
    hhs = 0
    if main_clinic:
        startkey = [clinic_id, request.dates.startdate.year, request.dates.startdate.month - 1]
        endkey = [clinic_id, request.dates.enddate.year, request.dates.enddate.month - 1, {}]
        results = get_db().view("reports/nhc_mortality_report", group=True, group_level=7,
                                startkey=startkey, endkey=endkey).all()
        for row in results:
            # key: ["5010", 2010,8,"adult","f","cause","heart_problem"]
            clinic_id_back, year, jsmonth, agegroup, gender, type, val = row["key"]
            count = row["value"]
            group = MortalityGroup(main_clinic, agegroup, gender)
            if type == "global":
                global_map[val] = count
            if type == "cause":
                cause_of_death_report.add_data(group, val, count)
            elif type == "place":
                place_of_death_report.add_data(group, val, count)
        if "num_households" in global_map:
            hhs = global_map.pop("num_households")
        global_display.add_data(global_map)
    
    
    districts = Location.objects.filter(type__slug="district").order_by("name")
    clinics = Location.objects.filter(type__slug="clinic").order_by("parent__name", "name")
    
    return render_to_response(request, "reports/mortality_register.html", 
                              {"show_dates": True, "cause_report": cause_of_death_report,
                               "place_report": place_of_death_report,
                               "districts": districts, 
                               "clinics": clinics, 
                               "global_display": global_display,
                               "hhs": hhs,
                               "main_clinic": main_clinic,
                               })
 

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
    Under-Five Performance Indicator Report
    """
    return _pi_report(request, "reports/under_5_pi")
        
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def adult_pi(request):
    """
    Adult Performance Indicator Report
    """
    return _pi_report(request, "reports/adult_pi")

    
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def pregnancy_pi(request):
    """
    Pregnancy Performance Indicator Report
    """
    return _pi_report(request, "reports/pregnancy_pi")
        
@permission_required("webapp.bhoma_view_pi_reports")
@wrap_with_dates()
def chw_pi(request):
    """
    CHW Performance Indicator Report
    """
    # This is currently defunct and combined with the single CHW report.
    chw_id = request.GET.get("chw", None)
    chws = CommunityHealthWorker.view("chw/by_clinic", include_docs=True)
    main_chw = CommunityHealthWorker.get(chw_id) if chw_id else None
    report = { "name": "CHW PI Report" }
    if main_chw:
        if not request.dates.is_valid():
            messages.error(request, request.dates.get_validation_reason())
        else:
            report = get_chw_pi_report(main_chw, request.dates.startdate, request.dates.enddate)
    return render_to_response(request, "reports/chw_pi.html", 
                              {"report": report, "chws": chws, "main_chw": main_chw})
    
def clinic_summary_raw(request, group_level=2):
    report = get_clinic_summary(group_level)
    body = render_report(report, template="reports/text/couch_report_raw.txt")
    return HttpResponse(body, content_type="text/plain")
    

def clinic_report(request, view_name):
    url = reverse(view_name)
    view, args, kwargs = resolve(url)
    options = TouchscreenOptions.default()
    options.header = view.__doc__
    options.backbutton = ButtonOptions(show=True, link=reverse("report_list"), text="BACK")

    return render_to_response(request, "reports/clinic_report_wrapper.html", 
                              {"options": options,
                               "url": url})

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

def clinic_health(clinic, sshinfo=[]):
    c = {
        'id': clinic.slug,
        'name': clinic.name,
        'active': False,
    }

    pings = Ping.objects.filter(tag=c['id'])
    if pings:
        c['active'] = True
        c['last_internet'] = pings.latest('at').at
        diff = datetime.now() - c['last_internet']
        if diff < timedelta(days=1):
            c['last_internet_status'] = 'good'
        elif diff < timedelta(days=4):
            c['last_internet_status'] = 'warn'
        else:
            c['last_internet_status'] = 'bad'

    def tunnel_entry(caption, data):
        e = {'caption': caption}
        if c['id'] in data:
            c['active'] = True
            uptime = data[c['id']][0]
            e['uptime'] = '%.1f%%' % (100. * uptime)
            if uptime > .35:
                e['status'] = 'good'
            elif uptime > .1:
                e['status'] = 'warn'
            else:
                e['status'] = 'bad'
        return e
    c['ssh_tunnel'] = [tunnel_entry(caption, data) for caption, data in sshinfo]

    latest_doc = get_db().view('bhomalog/recent_doc_by_clinic', reduce=True, key=str(c['id'])).first()
    if latest_doc:
        c['active'] = True
        c['last_doc_synced'] = datetime.fromtimestamp(latest_doc['value']['max'])
        diff = datetime.now() - c['last_doc_synced']
        if diff < timedelta(days=1):
            c['doc_sync_status'] = 'good'
        elif diff < timedelta(days=4):
            c['doc_sync_status'] = 'warn'
        else:
            c['doc_sync_status'] = 'bad'

    print dir(get_db().view('bhomalog/recent_doc_by_clinic', reduce=True, key=str(c['id'])))

    return c

def systems_health(req):
    clinics = Location.objects.filter(type__slug='clinic')

    def tally_ssh(logdata, window):
        now = datetime.now()
        return dict((str(TAGS[k]), v) for k, v in tally(logdata, now - window, now).iteritems())
    sshlog = parse_logfile()
    sshinfo = [(caption, tally_ssh(sshlog, window)) for caption, window in [
            ('12 hours', timedelta(hours=12)),
            ('24 hours', timedelta(days=1)),
            ('5 days', timedelta(days=5))
        ]]

    clinic_stats = [clinic_health(c, sshinfo=sshinfo) for c in clinics]
    clinic_stats.sort(key=lambda k: k['id'])

    return render_to_response(req, 'reports/systems_health.html', {'clinics': clinic_stats})
