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
from bhoma.apps.reports.display import ReportDisplay, ReportDisplayRow


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

@wrap_with_dates()
def under_five_pi(request):
    """
    Under five performance indicator report
    """
    return _couch_report(request, "reports/under_5_pi")
        
@wrap_with_dates()
def adult_pi(request):
    """
    Adult performance indicator report
    """
    return _couch_report(request, "reports/adult_pi")

    
@wrap_with_dates()
def pregnancy_pi(request):
    """
    Pregnancy performance indicator report
    """
    return _couch_report(request, "reports/pregnancy_pi")
        
@wrap_with_dates()
def chw_pi(request):
    """
    CHW performance indicator report
    """
    return _couch_report(request, "reports/chw_pi")
    
def _couch_report(request, view_name):
    """
    Generic report engine from couch.
    """
    results = get_db().view(view_name, group=True, group_level=3, 
                            **_get_keys(request.startdate, request.enddate)).all()
    report = ReportDisplay.from_view_results(results)
    return render_to_response(request, "reports/couch_report.html",
                              {"show_dates": True, "report": report})
    
def _get_keys(startdate, enddate):
    # set the start key to the first and the end key to the last of the month
    startkey = [settings.BHOMA_CLINIC_ID, startdate.year, startdate.month - 1]
    endkey = [settings.BHOMA_CLINIC_ID, enddate.year, enddate.month - 1]
    return {"startkey": startkey, "endkey": endkey}