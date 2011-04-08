from collections import defaultdict
from bhoma.apps.reports.shortcuts import get_monthly_submission_breakdown
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay, FractionalDisplayValue
from django.utils.datastructures import SortedDict
from bhoma.apps.zones.models import ClinicZone
import itertools
from bhoma.apps.reports.calc.chw import get_monthly_referral_breakdown,\
    get_monthly_case_breakdown, get_monthly_fu_breakdown,\
    get_monthly_danger_sign_referred_breakdown
from bhoma.apps.reports import const

def get_chw_pi_report(chw, startdate, enddate):
    chw_id = chw.get_id
    # I hate reports. This method is a mess
    
    form_map = {}
    # populate the form data
    form_map[config.CHW_HOUSEHOLD_SURVEY_NAMESPACE] = \
        get_monthly_submission_breakdown(chw_id, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE, startdate, enddate)
    form_map[config.CHW_FOLLOWUP_NAMESPACE] = \
        get_monthly_submission_breakdown(chw_id, config.CHW_FOLLOWUP_NAMESPACE, startdate, enddate)
    form_map[config.CHW_REFERRAL_NAMESPACE] = \
        get_monthly_submission_breakdown(chw_id, config.CHW_REFERRAL_NAMESPACE, startdate, enddate)
    
    
    final_map = defaultdict(lambda: [])
    
    def _val(num, denom, slug):
        """Populate report value object"""
        return FractionalDisplayValue(num, denom, slug, hidden=False, 
                                      display_name=const.get_display_name("chw_pi", slug),
                                      description=const.get_description("chw_pi", slug))
    # 1. Number of houses visited by each CHW / Total number of Households to be visited by the CHW per month 
    # (which should be 33% of their total households)
    # Numerator: HH form submissions
    # Denominator: # of hhs in zone / 3
    zone = chw.get_zone()
    if zone:
        for date, count in form_map[config.CHW_HOUSEHOLD_SURVEY_NAMESPACE].items():
            value_display = _val(count,zone.households/3, "hh_surveys")
            final_map[date].append(value_display)

    # 2.Number of patient follow-ups attempted by CHW X by target date / total number of patient 
    # follow-ups assigned to CHW X older than the target date
    # Numerator: Follow Up forms filled out
    # Denominator: Follow Ups assigned to CHW with due date in the report period
    case_breakdown = get_monthly_case_breakdown(chw, startdate, enddate)
    fu_dates = set(list(itertools.chain(case_breakdown.keys(), form_map[config.CHW_FOLLOWUP_NAMESPACE].keys())))
    for date in fu_dates:
        fu_got = case_breakdown[date] 
        fu_made = form_map[config.CHW_FOLLOWUP_NAMESPACE][date]
        value_display = _val(fu_made, fu_got, "fu_att")
        final_map[date].append(value_display)
            
    fu_breakdown = get_monthly_fu_breakdown(chw, startdate, enddate)
    # 3. Number of patient follow-ups with outcomes recorded before it becomes lost to follow up / 
    # total number of patient follow-ups assigned to CHW X
    # Numerator: Follow-Ups with "bhoma_close" equal to "true" with "bhoma_outcome" 
    #            not equal to "lost_to_followup_time_window"
    # Denominator: Follow Ups assigned to CHW with due date in the report period
    for date in fu_dates:
        fu_got = case_breakdown[date]
        fu_breakdown_month_success = fu_breakdown[date][True]
        success_fu_count = sum(val for key, val in fu_breakdown_month_success.items() if key != "lost_to_followup_time_window")
        value_display = _val(success_fu_count, fu_got, "fu_complete")
        final_map[date].append(value_display)
            
    # 4.  Total number of referrals that turn up at the clinic / Total Number of Referrals made by each CHW
    # Numerator: Visits with a matching referral ID
    # Denominator: Referrals
    ref_breakdown = get_monthly_referral_breakdown(chw, startdate, enddate)
    for date, count in form_map[config.CHW_REFERRAL_NAMESPACE].items():
        ref_found = ref_breakdown[date]
        value_display = _val(ref_found, count, "ref_turned_up")
        final_map[date].append(value_display)
    
    # 5.  Number of patient referrals with life-threatening complaints with subsequent clinic visit 
    # (match form to CHW either by CHW referral ID card or by circling referral ID on form) / 
    # Number of patients with life threatening complaint referred off referral form by CHW to clinic
    # Numerator: Visits with a matching referral ID that qualify as life-threatening
    # Denominator: Referrals
    """ todo
    ref_breakdown = get_monthly_referral_breakdown(chw, startdate, enddate)
    for date, count in form_map[config.CHW_REFERRAL_NAMESPACE].items():
        if date not in final_map:
            final_map[date] = []
        ref_found = ref_breakdown[date] and form_map[config.CHW_REFERRAL_NAMESPACE][life_threatening] == "y"
        value_display = FractionalDisplayValue(ref_found, count, config.CHW_REFERRAL_NAMESPACE, 
                                               hidden=False, display_name="Life Threatening Referrals Turned up at Clinic",
                                               description="")
        final_map[date].append(value_display)  
    
    """            
    
    # 6. Number of patients with danger signs referred from hh visit by CHW to clinic / 
    # Number of patients with danger signs on hh visit
    # Numerator: HH visits with danger signs and referred
    # Denominator: HH visits with danger signs
    danger_sign_breakdown = get_monthly_danger_sign_referred_breakdown(chw, startdate, enddate)
    for date, (num, denom) in danger_sign_breakdown.items():
        value_display = _val(num, denom, "danger_sign_ref")
        final_map[date].append(value_display)
    report_name = "CHW PI Summary for %s" % chw.formatted_name
    
    all_rows = []
    for date, rows in final_map.items():
        keys = SortedDict()
        keys["Year"] = date.year
        keys["Month"] = date.month
        all_rows.append(ReportDisplayRow(report_name, keys, rows))
    return ReportDisplay(report_name, all_rows)
    
    
    