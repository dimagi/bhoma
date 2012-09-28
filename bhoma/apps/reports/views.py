import json
from django.conf import settings
from bhoma.apps.case.models import CReferral
from dimagi.utils.web import render_to_response
from dimagi.utils.couch.database import get_db
from dimagi.utils.dates import add_months, DateSpan, months_between
from bhoma.apps.xforms.util import get_xform_by_namespace
from collections import defaultdict
import bhoma.apps.xforms.views as xforms_views
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, resolve
from bhoma.apps.reports.display import PIReport, AggregateReport
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
from bhoma.apps.locations.util import clinic_display_name, clinics_for_view,\
    districts_for_view
from bhoma.apps.reports.flot import get_sparkline_extras
from bhoma.apps.webapp.config import is_clinic
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions
from bhoma.apps.webapp.models import Ping
from bhoma.apps.reports.calc.summary import get_clinic_summary
from bhoma.apps.reports.calc.mortailty import MortalityGroup, MortalityReport,\
    CauseOfDeathDisplay, AGGREGATE_OPTIONS
from datetime import datetime, timedelta
from bhoma.apps.reports.shortcuts import get_last_submission_date,\
    get_first_submission_date, get_forms_submitted, get_submission_breakdown,\
    get_recent_forms
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.calc.pi import get_chw_pi_report, ChwPiReport,\
    ChwPiReportDetails
from bhoma.scripts.reversessh_tally import parse_logfile, tally, REMOTE_CLINICS
from django.db.models import Q
from dimagi.utils.dates import delta_secs
from bhoma.apps.reports import const
from bhoma.apps.xforms.models import CXFormInstance
from bhoma.apps.patient.models import CPatient
from dimagi.utils.decorators.datespan import datespan_in_request
from bhoma.apps.reports.models import PregnancyReportRecord
import itertools
from bhoma.apps.phone.models import SyncLog
from bhoma.apps.reports.calc.forms import forms_submitted
from bhoma.apps.zones.models import ClinicZone
from StringIO import StringIO
from couchexport.export import export_raw, FormattedRow
from couchexport.shortcuts import export_response

DATE_FORMAT_STRING = "%b %Y"

def report_list(request):
    template = "reports/report_list_ts.html" if is_clinic() else "reports/report_list.html"
    return render_to_response(request, template, {"options": TouchscreenOptions.default()})

def clinic_summary(request, group_level=2):
    """Clinic Summary Report"""
    report = get_clinic_summary(group_level)
    return render_to_response(request, "reports/couch_report.html",
                              {"show_dates": False, "report": report})
    
@permission_required("webapp.bhoma_administer_clinic")
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
@permission_required("webapp.bhoma_administer_clinic")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def single_chw_summary(request):
    """Report for a single CHW""" 
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
        
        if not request.datespan.is_valid():
            messages.error(request, request.datespan.get_validation_reason())
            messages.warning(request, "Performance Indicators are not displayed. Please fix the other errors")
            report = {"name": "Partial CHW Summary for %s" % main_chw.formatted_name}
        else:
            report = get_chw_pi_report(main_chw, request.datespan.startdate, request.datespan.enddate)
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

@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def mortality_register(request):
    if not request.datespan.is_valid():
        messages.error(request, request.datespan.get_validation_reason())
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
        startkey = [clinic_id, request.datespan.startdate.year, request.datespan.startdate.month - 1]
        endkey = [clinic_id, request.datespan.enddate.year, request.datespan.enddate.month - 1, {}]
        results = get_db().view("centralreports/nhc_mortality_report", group=True, group_level=7,
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
    
    return render_to_response(request, "reports/mortality_register.html", 
                              {"show_dates": True, "cause_report": cause_of_death_report,
                               "place_report": place_of_death_report,
                               "districts": districts_for_view(), 
                               "clinics": clinics_for_view(), 
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
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def under_five_pi(request):
    """
    Under-Five Performance Indicator Report
    """
    return _pi_report(request, "under_5_pi")
        
@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def adult_pi(request):
    """
    Adult Performance Indicator Report
    """
    return _pi_report(request, "adult_pi")

    
@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def pregnancy_pi(request):
    """
    Pregnancy Performance Indicator Report
    """
    return _pi_report(request, "pregnancy_pi")

def _export_pis(report, report_slug, non_data_cols=3):
    context = report.get_data(include_urls=False)
    
    
    # THESE FUNCTIONS ARE TOTAL HACKS.
    # they rely on knowing the first two or three values are clinic, year, month,
    # and then the rest are fractional
    def _transform_headings(headings, non_data_cols):
        ret = headings[:non_data_cols]
        for h in headings[non_data_cols:]:
            ret.append("%s num" % h)
            ret.append("%s denom" % h)
            ret.append("%s pct" % h)
        return ret
    
    def _transform_rows(rows, non_data_cols):
        return [_transform_values(r, non_data_cols) for r in rows]
    
    def _transform_values(values, non_data_cols):
        ret = values[:non_data_cols]
        for v in values[non_data_cols:]:
            if v != "N/A":
                for special in "(/)":
                    v = v.replace(special, " ")
                pct, num, denom = v.split()
                ret.extend([num, denom, pct])
            else:
                ret.extend(["N/A"] * 3)
        return ret
    
    temp = StringIO()
    export_raw((("data", _transform_headings(context["headings"], non_data_cols)),),
               (("data", _transform_rows(context["rows"], non_data_cols)),), temp)
    return export_response(temp, "xlsx", report_slug)

@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def export_pis(request, report_slug):
    clinic_id = request.GET.get("clinic", None)
    results = _pi_results(report_slug, request.datespan.startdate, request.datespan.enddate,
                          clinic_id) 
    report = PIReport.from_view_results(report_slug, results)
    return _export_pis(report, report_slug)


@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def export_chw_pis(request):
    report_slug = "chw_pi"
    chw_id = request.GET.get("chw", None)
    main_chw = CommunityHealthWorker.get(chw_id) 
    report = get_chw_pi_report(main_chw, request.datespan.startdate, request.datespan.enddate)
    return _export_pis(report, report_slug, non_data_cols=2)

@require_GET
@permission_required("webapp.bhoma_view_pi_reports")
def pi_details(request):
    year = int(request.GET["year"])
    month = int(request.GET["month"])
    clinic = request.GET["clinic"]
    report_slug = request.GET["report"]
    col_slug = request.GET["col"]
    results = get_db().view(const.get_view_name(report_slug), reduce=False,
                            key=[year, month -1, clinic, col_slug], include_docs=True)
    forms = []
    for row in results:
        num, denom = row["value"]
        # only count forms for now, and make sure they have a patient id 
        # and contributed to the report denominator
        if row["doc"]["doc_type"] == "CXFormInstance" and denom > 0:
            form = CXFormInstance.wrap(row["doc"])
            try:
                form.patient_id = form.xpath("case/patient_id")
                form.bhoma_patient_id = CPatient.get(form.patient_id).formatted_id
            except ResourceNotFound:
                form.patient = None
            form.num = num
            form.denom = denom
            form.good = num == denom
            forms.append(form)
        elif row["doc"]["doc_type"] == "PregnancyReportRecord" and denom > 0:
            # for the pregnancy PI force the aggregated pregnancy docs
            # to look like forms 
            preg = PregnancyReportRecord.wrap(row["doc"])
            try:
                preg.bhoma_patient_id = CPatient.get(preg.patient_id).formatted_id
            except ResourceNotFound:
                form.patient = None
            preg.num = num
            preg.denom = denom
            preg.good = num == denom
            preg.encounter_date = preg.first_visit_date
            forms.append(preg)  
        
    title = "PI Details - %s: %s (%s, %s)" % (const.get_name(report_slug), 
                                              const.get_display_name(report_slug, col_slug),
                                              datetime(year, month, 1).strftime("%B %Y"),
                                              clinic_display_name(clinic))   
                                             
    return render_to_response(request, "reports/pi_details.html", 
                              {"report": {"name": title},
                               "forms": forms})

@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
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
        if not request.datespan.is_valid():
            messages.error(request, request.datespan.get_validation_reason())
        else:
            report = get_chw_pi_report(main_chw, request.datespan.startdate, request.datespan.enddate)
    return render_to_response(request, "reports/chw_pi.html",
                              {"report": report, "chws": chws, 
                               "main_chw": main_chw,
                               "view_slug": "chw_pi"})
    
@require_GET
@permission_required("webapp.bhoma_view_pi_reports")
def chw_pi_details(request):
    year = int(request.GET["year"])
    month = int(request.GET["month"])
    
    chw_id = request.GET["chw"]
    col_slug = request.GET["col"]
    
    chw = CommunityHealthWorker.get(chw_id)
    report = ChwPiReportDetails(chw, year, month, col_slug)
    return render_to_response(request, "reports/chw_pi_details.html", 
                              {"report": report })
                               

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

def _pi_report(request, view_slug):
    """
    Generic report engine for the performance indicator reports
    """
    if not request.datespan.is_valid():
        messages.error(request, request.datespan.get_validation_reason())
        return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": True, "report": None})
                               
                                   
    clinic_id = request.GET.get("clinic", None)
    results = _pi_results(view_slug, request.datespan.startdate, request.datespan.enddate,
                          clinic_id) 
    report = PIReport.from_view_results(view_slug, results)
    
    main_clinic = Location.objects.get(slug=clinic_id) if clinic_id else None
    return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": False, 
                               "hide_districts": True, 
                               "main_clinic": main_clinic,
                               "clinics": clinics_for_view(),
                               "districts": districts_for_view(),
                               "view_slug": view_slug,
                               "report": report})

def _pi_results(view_slug, startdate, enddate, clinic_id):
    # keys is a list of start/end key dicts, for all of them, 
    # get the results and chain into one big single list
    return itertools.chain(*[get_db().view\
                             (const.get_view_name(view_slug), group=True, 
                              group_level=4, **keys).all() \
                              for keys in _get_keys(startdate, enddate, clinic_id)])
    
def _get_keys(startdate, enddate, clinic_id):
    # assumes the start date is set to the first the end date to the last of the month
    # if there's no clinic specified just use the whole range
    if not clinic_id:
        startkey = [startdate.year, startdate.month - 1]
        endkey = [enddate.year, enddate.month - 1, {}]
        return [{"startkey": startkey, "endkey": endkey}]
    else:
        # otherwise only include results for this clinic
        return [{"startkey": [year, month - 1, clinic_id],
                 "endkey": [year, month -1, clinic_id, {}]} \
                 for year, month in months_between(startdate, enddate)]
    
def fmt_time(dt):
    h_ago = int(round(delta_secs(datetime.now() - dt) / 3600.))
    days = h_ago / 24
    hours = h_ago % 24
    str_ago = ', '.join(filter(lambda s: s, [
                '%d day%s' % (days, 's' if days != 1 else '') if days > 0 else '',
                '%d hour%s' % (hours, 's' if hours != 1 else '') if (hours > 0 and days < 4) or days == 0 else ''
            ]))
    return {'date': dt, 'ago': '%s ago' % str_ago}

    
def clinic_health(clinic_dict, sshinfo=[]):
    c = clinic_dict
    if c['type'] == 'district':
        c['name'] += ' District'

    pings = Ping.objects.filter(tag=c['id'])
    if pings:
        c['active'] = True
        latest_ping = pings.latest('at')
        last_internet = latest_ping.at
        try:
            c['version'] = json.loads(latest_ping.payload)['version'][:7]
        except:
            pass
        diff = datetime.now() - last_internet
        c['last_internet'] = fmt_time(last_internet)
        if diff < timedelta(days=1):
            c['last_internet_status'] = 'good'
        elif diff < timedelta(days=4):
            c['last_internet_status'] = 'warn'
        else:
            c['last_internet_status'] = 'bad'

    def tunnel_entry(caption, data):
        e = {'caption': caption}
        if c['id'] in data:
            uptime = data[c['id']][0]
            if uptime > 0:
                c['active'] = True
            e['uptime'] = '%.1f%%' % (100. * uptime)
            if uptime > .35:
                e['status'] = 'good'
            elif uptime > .1:
                e['status'] = 'warn'
            else:
                e['status'] = 'bad'
        return e
    c['ssh_tunnel'] = [tunnel_entry(caption, data) for caption, data in sshinfo]

    if c['type'] == 'clinic':
        latest_doc = get_db().view('centralreports/recent_doc_by_clinic', reduce=True, key=str(c['id'])).first()
        if latest_doc:
            c['active'] = True
            last_doc_synced = datetime.fromtimestamp(latest_doc['value']['max'])
            diff = datetime.now() - last_doc_synced
            c['last_doc_synced'] = fmt_time(last_doc_synced)
            if diff < timedelta(days=1):
                c['doc_sync_status'] = 'good'
            elif diff < timedelta(days=4):
                c['doc_sync_status'] = 'warn'
            else:
                c['doc_sync_status'] = 'bad'

    return c

def chw_dashboard_summary(clinic_dict):
    
    def _status_from_last_sync(last_sync):
        diff = datetime.utcnow() - last_sync.date if last_sync else None
        if not diff or diff > timedelta(days=5):
            return "bad"
        elif diff > timedelta(days=3):
            return "warn"
        else:
            return "good"
        
    def _fmt_hh_visits(num_visits, chw):
        ret = {}
        ret["count"] = num_visits
        
        zone = chw.get_zone()
        # > 100% of quota for the month in 30 days: green
        # 50 - 100% of quota for the month in 30 days: yellow
        # < 50% of quota for the month in 30 days: red
        # the quota is # of hh's in the zone / 3
        if zone:
            ret["households"] = zone.households
            ret["percent"] = float(100) * float(num_visits) / float(zone.households)  
            if num_visits > zone.households / 3:
                ret["status"] = "good"
            elif num_visits > zone.households / (2 * 3):
                ret["status"] = "warn"
            else: 
                ret["status"] = "bad"
        else:
            ret["percent"] = "?"
            ret["households"] = "?"
            ret["status"] = "unknown"
        return ret
    
    def _status_from_ref_visits(ref_visits):
        if ref_visits > 2:
            return "good"
        elif ref_visits > 0:
            return "warn"
        else: 
            return "bad"
        
    def _status_from_overdue_fus(fus):
        if fus > 2:
            return "bad"
        elif fus > 0:
            return "warn"
        else: 
            return "good"
        
    chws = filter(lambda chw: chw.user and chw.user.is_active,
                  CommunityHealthWorker.view("chw/by_clinic", key=clinic_dict["id"],
                                             include_docs=True).all())
    if chws:
        clinic_dict["active"] = True
        clinic_dict["chws"] = []
        for chw in chws:
            
            chw_dict = {
                "id":   chw.get_id,
                "name": chw.formatted_name,
                "zone": chw.current_clinic_zone 
            }
            # Metrics per CHW:
            # - date/time of last sync
            last_sync = SyncLog.view("phone/sync_logs_by_chw", reduce=False, 
                                     startkey=[chw.get_id, {}], endkey=[chw.get_id], 
                                     include_docs=True, limit=1, descending=True).one()
            chw_dict["last_sync"] = fmt_time(last_sync.date) if last_sync else None
            chw_dict["last_sync_status"] = _status_from_last_sync(last_sync)
            
            end = datetime.today() + timedelta(days=1)
            start = end - timedelta(days=30)
            
            # - current outstanding follow ups
            # Any follow up assigned to the CHW's clinic/zone that is past due
            # and not closed. This is different from the PI in that it won't
            # check whether or not the CHW has had that case sync down to their
            # phone or not.
            # This is much faster to calculate than anything else.
            res = get_db().view("centralreports/cases_due",
                                startkey=[chw.current_clinic_id, chw.current_clinic_zone, 0],
                                endkey=[chw.current_clinic_id, chw.current_clinic_zone, 
                                        end.year, end.month - 1, end.day],
                                reduce=True).one()
            chw_dict["overdue_fus"] = res["value"] if res else 0
            chw_dict["overdue_fus_status"] = _status_from_overdue_fus(chw_dict["overdue_fus"])
                        
            # - visits performed
            chw_dict["hh_visits"] = _fmt_hh_visits(forms_submitted\
                (chw.get_id, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE,
                 start, end), chw)
            
            # - referrals made
            chw_dict["ref_visits"] = forms_submitted\
                (chw.get_id, config.CHW_REFERRAL_NAMESPACE,
                 start, end)
            chw_dict["ref_visits_status"] = _status_from_ref_visits(chw_dict["ref_visits"])
            
            clinic_dict["chws"].append(chw_dict)
        
        # sort
        clinic_dict["chws"].sort(key=lambda k: k['zone'])
            
    return clinic_dict
    
def clinic_dict_from_clinic(clinic, active=False):
    return {
        'id': clinic.slug,
        'name': clinic.name,
        'type': clinic.type.slug,
        'active': active,
    }
    
def dhmt_dict_from_district(district):
    return {
        "id": "%sDHMT" % district.slug, # this must magically match the codes used in phonehome
        "name": "%s DHMT" % district.name,
        "type": "dhmt",
        "active": False
    }


@permission_required("webapp.bhoma_view_pi_reports")
@datespan_in_request(from_param="startdate", to_param="enddate",
                     format_string=DATE_FORMAT_STRING)
def disease_aggregates(request):
    if not request.datespan.is_valid():
        messages.error(request, request.datespan.get_validation_reason())
        return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": True, "report": None})
                               
                                   
    clinic_id = request.GET.get("clinic", None)
    slug = "disease_aggregate"
    results = _pi_results(slug, request.datespan.startdate, request.datespan.enddate,
                          clinic_id)
    
    main_clinic = Location.objects.get(slug=clinic_id) if clinic_id else None
    report = AggregateReport.from_view_results(slug, results)
    
    return render_to_response(request, "reports/pi_report.html",
                              {"show_dates": False, 
                               "hide_districts": True, 
                               "main_clinic": main_clinic,
                               "clinics": clinics_for_view(),
                               "districts": districts_for_view(),
                               "view_slug": slug,
                               "report": report})

    
@require_GET
@permission_required("webapp.bhoma_view_pi_reports")
def disease_details(request):
    year = int(request.GET["year"])
    month = int(request.GET["month"])
    clinic = request.GET["clinic"]
    report_slug = request.GET["report"]
    col_slug = request.GET["col"]
    results = get_db().view(const.get_view_name(report_slug), reduce=True,
                            startkey=[year, month -1, clinic, col_slug], 
                            endkey=[year, month -1, clinic, col_slug, {}],
                            group=True, group_level=5)
    results_dict = dict([(row["key"][4], row["value"]) for row in results])
    title = "Clinic: %s, Category: %s, %s" % \
        (clinic_display_name(clinic), 
         const.get_display_name(report_slug, col_slug),
         datetime(year, month, 1).strftime("%B, %Y"))   
    
    return render_to_response(request, "reports/disease_details.html", 
                              {"report": {"name": title},
                               "values": results_dict})

    
@permission_required("webapp.bhoma_administer_clinic")
def chw_dashboard(req):
    clinic_stats = [chw_dashboard_summary(clinic_dict_from_clinic(c)) \
                    for c in Location.objects.filter(type__slug='clinic')]
    district_stats = [clinic_dict_from_clinic(c, active=True) \
                      for c in Location.objects.filter(type__slug='district')]
    
    clinic_stats.extend(district_stats)
    clinic_stats.sort(key=lambda k: k['id'])
    
    return render_to_response(req, "reports/chw_dashboard.html", 
                              {"clinics": clinic_stats})

def systems_health(req):
    remote_sites = Location.objects.filter(Q(type__slug='clinic') | Q(type__slug='district'))

    def reversessh_slug_to_id(tag):
        return str(dict((v, k) for k, v in REMOTE_CLINICS.iteritems())[tag])

    def tally_ssh(logdata, window):
        now = datetime.now()
        return dict((reversessh_slug_to_id(k), v) for k, v in tally(logdata, now - window, now).iteritems())
    
    sshlog = parse_logfile()
    sshinfo = [(caption, tally_ssh(sshlog, window)) for caption, window in [
            ('12 hours', timedelta(hours=12)),
            ('24 hours', timedelta(days=1)),
            ('5 days', timedelta(days=5))
        ]]

    clinic_stats = [clinic_health(clinic_dict_from_clinic(c), sshinfo=sshinfo) for c in remote_sites]
    clinic_stats.extend([clinic_health(dhmt_dict_from_district(d), sshinfo=sshinfo) \
                         for d in remote_sites.filter(type__slug="district")])
    
    clinic_stats.sort(key=lambda k: k['id'])

    return render_to_response(req, 'reports/systems_health.html', {'clinics': clinic_stats})
