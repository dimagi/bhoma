import calendar
from django.conf import settings
from bhoma.apps.case.models import CReferral
from bhoma.utils import render_to_response
from bhoma.utils.couch.database import get_db
from bhoma.apps.reports.decorators import wrap_with_dates


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
def under_five_pi(request):
    """
    Under five performance indicator report
    """
    results = get_db().view("reports/under_5_pi", group=True, group_level=3, **_get_keys(request.startdate, request.enddate)).all()
    return render_to_response(request, "reports/pi/under_five.html",
                              {"show_dates": True, "data": results })
    
@wrap_with_dates()
def adult_pi(request):
    """
    Adult performance indicator report
    """
    results = get_db().view("reports/under_5_pi", group=True, group_level=3, **_get_keys(request.startdate, request.enddate)).all()
    return render_to_response(request, "reports/pi/adult.html",
                              {"show_dates": True, "data": results })
    
@wrap_with_dates()
def pregnancy_pi(request):
    """
    Pregnancy performance indicator report
    """
    results = get_db().view("reports/under_5_pi", group=True, group_level=3, **_get_keys(request.startdate, request.enddate)).all()
    return render_to_response(request, "reports/pi/pregnancy.html",
                              {"show_dates": True, "data": results })
    
@wrap_with_dates()
def chw_pi(request):
    """
    CHW performance indicator report
    """
    results = get_db().view("reports/under_5_pi", group=True, group_level=3, **_get_keys(request.startdate, request.enddate)).all()
    return render_to_response(request, "reports/pi/chw.html",
                              {"show_dates": True, "data": results })
    
def _get_keys(startdate, enddate):
    # set the start key to the first and the end key to the last of the month
    startkey = [settings.BHOMA_CLINIC_ID, startdate.year, startdate.month - 1, 1]
    endkey = [settings.BHOMA_CLINIC_ID, enddate.year, enddate.month - 1, 
              calendar.monthrange(enddate.year, enddate.month)[1]]
    return {"startkey": startkey, "endkey": endkey}