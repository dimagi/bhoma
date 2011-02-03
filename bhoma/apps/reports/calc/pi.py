from collections import defaultdict
from bhoma.apps.reports.shortcuts import get_monthly_submission_breakdown
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay
from django.utils.datastructures import SortedDict

def get_chw_pi_report(chw, startdate, enddate):
    chw_id = chw.get_id
    #1. Number of houses visited by each CHW / Total number of Households to be visited by the CHW per month 
    # (which should be 33% of their total households)
    # The numerator here should be the number of household visit forms filled out by the CHW.  
    # There is a number in the CHW Monthly survey where they self report the number of households 
    # visited, but this encourages them to use the phone for each visit.  Note that we are 
    # currently unable to tell unique households - but would just sum forms submitted by user. 
    def _add_data(data_map, namespace, display):
        breakdown = get_monthly_submission_breakdown(chw_id, namespace, startdate, enddate)
        for date, count in breakdown.items():
            if date not in data_map:
                data_map[date] = []
            value_display = NumericalDisplayValue(count,namespace, hidden=False,
                                                  display_name=display, description="")
            data_map[date].append(value_display)
    
    date_map = {}
    _add_data(date_map, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE, "Household Surveys")
    _add_data(date_map, config.CHW_REFERRAL_NAMESPACE, "New Referrals")
    _add_data(date_map, config.CHW_FOLLOWUP_NAMESPACE, "Follow Ups")
    
    report_name = "CHW summary for %s" % chw.formatted_name
    
    all_rows = []
    for date, rows in date_map.items():
        keys = SortedDict()
        keys["Year"] = date.year
        keys["Month"] = date.month
        all_rows.append(ReportDisplayRow(report_name, keys, rows))
    return ReportDisplay(report_name, all_rows)
    
    # this returns a dictionary of {date: count} for each month where there were forms
    # 2.Number of houses visited by each CHW / Total number of Households to be visited by the CHW per quarter (which should be 100% of their total households)
    # Same numerator as above. 
    #3. Total Number of Clinic referrals made for each CHW / Total number of Referrals followed up by the CHW
    # I think you mean Follow Ups here.  Rewording : "Total number of Follow Ups assigned to the CHW / Number of Follow-Ups that the CHW follows up. 
    #4. Total Number of Referrals made by each CHW / Total number of referrals that turn up at the clinic
    