from collections import defaultdict
from bhoma.apps.reports.shortcuts import get_monthly_submission_breakdown
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay, FractionalDisplayValue
from django.utils.datastructures import SortedDict
from bhoma.apps.zones.models import ClinicZone
import itertools
from bhoma.apps.reports.calc.chw import get_monthly_referral_breakdown,\
    get_monthly_case_breakdown

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
    
    
    final_map = {}
    # 1. Number of houses visited by each CHW / Total number of Households to be visited by the CHW per month 
    # (which should be 33% of their total households)
    # Numerator: HH form submissions
    # Denominator: # of hhs in zone / 3
    zone = chw.get_zone()
    if zone:
        for date, count in form_map[config.CHW_HOUSEHOLD_SURVEY_NAMESPACE].items():
            if date not in final_map:
                final_map[date] = []
            value_display = FractionalDisplayValue(count,zone.households/3, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE, 
                                                   hidden=False, display_name="Household Surveys Completed",
                                                   description="")
            final_map[date].append(value_display)
            
    # 2.Number of houses visited by each CHW / Total number of Households to be visited by the CHW per quarter 
    # (which should be 100% of their total households)
    # Same numerator as above. 
    # TODO / remove
    
    # 3. Total number of Follow Ups assigned to the CHW / Number of Follow-Ups that the CHW follows up.
    # Numerator: Follow Ups assigned to CHW with due date in the report period
    # Denominator: Follow up forms submitted (need more conditions?)
    case_breakdown = get_monthly_case_breakdown(chw, startdate, enddate)
    fu_dates = set(list(itertools.chain(case_breakdown.keys(), form_map[config.CHW_FOLLOWUP_NAMESPACE].keys())))
    for date in fu_dates:
        if date not in final_map:
            final_map[date] = []
        fu_got = case_breakdown[date]
        fu_made = form_map[config.CHW_FOLLOWUP_NAMESPACE][date]
        value_display = FractionalDisplayValue(fu_made, fu_got, config.CHW_FOLLOWUP_NAMESPACE, 
                                               hidden=False, display_name="Clinic Follow Ups Made",
                                               description="")
        final_map[date].append(value_display)
            
    # 4. Total Number of Referrals made by each CHW / Total number of referrals that turn up at the clinic
    # Numerator: Referrals
    # Denominator: Visits with a matching referral ID
    ref_breakdown = get_monthly_referral_breakdown(chw, startdate, enddate)
    for date, count in form_map[config.CHW_REFERRAL_NAMESPACE].items():
        if date not in final_map:
            final_map[date] = []
        ref_found = ref_breakdown[date]
        value_display = FractionalDisplayValue(ref_found, count, config.CHW_REFERRAL_NAMESPACE, 
                                               hidden=False, display_name="Referrals Turned up at Clinic",
                                               description="")
        final_map[date].append(value_display)
        
    report_name = "CHW PI Summary for %s" % chw.formatted_name
    
    
    all_rows = []
    for date, rows in final_map.items():
        keys = SortedDict()
        keys["Year"] = date.year
        keys["Month"] = date.month
        all_rows.append(ReportDisplayRow(report_name, keys, rows))
    return ReportDisplay(report_name, all_rows)
    
    
    