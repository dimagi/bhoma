from collections import defaultdict
from bhoma.apps.reports.shortcuts import get_monthly_submission_breakdown,\
    get_forms_in_window
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay, FractionalDisplayValue, CHWPIReportDisplayRow
from django.utils.datastructures import SortedDict
from bhoma.apps.zones.models import ClinicZone
import itertools
from bhoma.apps.reports.calc.chw import get_monthly_referral_breakdown,\
    get_monthly_case_breakdown, get_monthly_fu_breakdown,\
    get_monthly_danger_sign_referred_breakdown, get_referrals_made,\
    get_referrals_found, get_monthly_case_list, followup_made,\
    successful_followup_made
from bhoma.apps.reports import const
from datetime import datetime, time, timedelta
from django.template.loader import render_to_string
from bhoma.apps.case.models.couch import CommCareCase
from bhoma.apps.patient.models.couch import CPatient
from dimagi.utils.couch.database import get_db

def _val(num, denom, slug):
    """Populate report value object"""
    return FractionalDisplayValue(num, denom, slug, hidden=False, 
                                  display_name=const.get_display_name("chw_pi", slug),
                                  description=const.get_description("chw_pi", slug))
    
def cached():
    """
    This decorator currently only works on object methods and 
    ones that take in no arguments besides self.
    
    It could be made more generic but is currently only serving
    a single purpose.
    """
    def wrapper(f):
        def with_cache(self):
            if not hasattr(self, "_cache"):
                self._cache = {}
            if not f in self._cache:
                self._cache[f] = f(self)
                
            return self._cache[f]
            
        return with_cache
    return wrapper

class ChwPiReport(object):
    """
    A container for the CHW PI report.
    """
    def __init__(self, chw, startdate, enddate):
        self._cache = {}
        self.chw = chw
        self.startdate = startdate
        self.enddate = enddate
    
    @property
    def chw_id(self):
        return self.chw.get_id
    
    @property 
    def report_name(self):
        return "CHW PI Summary for %s" % self.chw.formatted_name
    
    @cached()
    def fu_submission_breakdown(self):
        """
        Get the number of followup forms submitted broken down
        by month.
        """
        return get_monthly_submission_breakdown\
                    (self.chw_id, config.CHW_FOLLOWUP_NAMESPACE, 
                     self.startdate, self.enddate)
        
    @cached()
    def hh_submission_breakdown(self):
        """
        Get the number of household survey forms submitted broken down
        by month.
        """
        return get_monthly_submission_breakdown\
                (self.chw_id, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE, 
                 self.startdate, self.enddate)
    @cached()
    def referral_submission_breakdown(self):
        """
        Get the number of referral forms submitted broken down
        by month.
        """
        return get_monthly_submission_breakdown\
                    (self.chw_id, config.CHW_REFERRAL_NAMESPACE, 
                     self.startdate, self.enddate)
    
    @cached()
    def case_breakdown(self):
        """
        Gets CommCareCase objects assigned to the CHW that were due in a given 
        month. 
        
        Returns a dictionary mapping dates to the number of cases from that month.
        """
        return get_monthly_case_breakdown(self.chw, self.startdate, 
                                          self.enddate)
            
    @cached()
    def case_list(self):
        return get_monthly_case_list(self.chw, self.startdate, self.enddate)
    
    @cached()
    def fu_breakdown(self):
        return get_monthly_fu_breakdown(self.chw, self.startdate, self.enddate)
    
    @cached()
    def referral_breakdown(self):
        return get_monthly_referral_breakdown(self.chw, self.startdate, 
                                              self.enddate)
    
    @cached()
    def danger_sign_breakdown(self):
        return get_monthly_danger_sign_referred_breakdown(self.chw, self.startdate, 
                                                          self.enddate)
    @cached()
    def fu_dates(self):
        """
        Return a set of all dates (months) where there were cases due or 
        followups made.
        """
        return set(list(itertools.chain(self.case_breakdown().keys(), 
                                        self.fu_submission_breakdown().keys())))
    
    @cached()
    def hh_surveys(self):
        """
        Get HH survey PI values
        """
        # 1. Number of houses visited by each CHW / Total number of Households to be visited by the CHW per month 
        # (which should be 33% of their total households)
        # Numerator: HH form submissions
        # Denominator: # of hhs in zone / 3
        zone = self.chw.get_zone()
        if zone:
            return ((date, _val(count,zone.households/3, "hh_surveys")) \
                    for date, count in self.hh_submission_breakdown().items())
        return []
    
    @cached()
    def fu_att(self):
        # 2.Number of patient follow-ups attempted by CHW X by target date / total number of patient 
        # follow-ups assigned to CHW X older than the target date
        # Numerator: Number of followups in the denominator that have at least 1 FU form submitted
        # Denominator: Number of followups sent to the CHW within the report period
        
        ret = []
        monthly_case_breakdown = self.case_list()
        for date in monthly_case_breakdown:
            fu_got = len(monthly_case_breakdown[date])
            fu_made = len([case_id for case_id in monthly_case_breakdown[date] if followup_made(case_id)])
            value_display = _val(fu_made, fu_got, "fu_att")
            ret.append((date, value_display))
        
        return ret
    
    @cached()
    def fu_complete(self):
        # 3. Number of patient follow-ups with outcomes recorded before it becomes lost to follow up / 
        # total number of patient follow-ups assigned to CHW X
        # Numerator: Follow-Ups with "bhoma_close" equal to "true" with "bhoma_outcome" 
        #            not equal to "lost_to_followup_time_window"
        # Denominator: Number of followups sent to the CHW within the report period
        ret = []
        monthly_case_breakdown = self.case_list()
        for date in monthly_case_breakdown:
            fu_got = len(monthly_case_breakdown[date])
            fus_made = [CommCareCase.get_by_id(case_id) \
                        for case_id in monthly_case_breakdown[date] \
                        if followup_made(case_id)]
            success_count = len([case for case in fus_made if successful_followup_made(case)])
            
            value_display = _val(success_count, fu_got, "fu_complete")
            ret.append((date, value_display))
        
        return ret
    
    @cached()
    def ref_turned_up(self):
        # 4.  Total number of referrals that turn up at the clinic / Total Number of Referrals made by each CHW
        # Numerator: Visits with a matching referral ID
        # Denominator: Referrals
        ret = []
        for date, data in self.referral_breakdown().items():
            value_display = _val(data["found"], data["made"], "ref_turned_up")
            ret.append((date, value_display))
        return ret
    
    @cached()
    def danger_sign_ref(self):
        # 6. Number of patients with danger signs referred from hh visit by CHW to clinic / 
        # Number of patients with danger signs on hh visit
        # Numerator: HH visits with danger signs and referred
        # Denominator: HH visits with danger signs
        return ((date, _val(num, denom, "danger_sign_ref")) for \
                 date, (num, denom) in self.danger_sign_breakdown().items())
    
    def _unimplemented_indicator_5(self):
        # This is left to serve as documentation when we implement this
        
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
    
    @cached()
    def get_full_datemap(self):
        final_map = defaultdict(lambda: [])
    
        for col in const.get_cols("chw_pi"):
            for date, val in self.get_for_slug(col):
                final_map[date].append(val)
        
        return final_map
        
    
    @cached()
    def get_display_object(self):
        all_rows = []
        for date, rows in self.get_full_datemap().items():
            keys = SortedDict()
            keys["Year"] = date.year
            keys["Month"] = date.month
            all_rows.append(CHWPIReportDisplayRow(self.chw_id, self.report_name, keys, rows))
        return ReportDisplay(self.report_name, all_rows)
    
    def get_for_slug(self, slug):
        """
        Given a slug, get the report values.
        
        Returns a list of tuples of the format:
        (date, value)
        """
        return getattr(self, slug)()
        
        
class ChwPiReportDetails(object):
    """
    Object to couple a chw pi report with a details view.
    """
    
    def __init__(self, chw, year, month, slug):
        self.year = year
        self.month = month
        self.slug = slug
        self.chw = chw
        self.startdate = datetime(year, month, 1)
        self.enddate = datetime(year + (month + 1) / 12, (month + 1) % 12, 1) - timedelta(days=1)
        self.report = ChwPiReport(chw, self.startdate, self.enddate)
        
    @property
    def name(self):
        return "%(report)s: %(column)s (%(chw)s, %(date)s)" % \
                {"report": const.get_name("chw_pi"), 
                 "chw": self.chw.formatted_name,
                 "column": const.get_display_name("chw_pi", self.slug),
                 "date": datetime(self.year, self.month, 1).strftime("%B %Y")}
    
    def _not_implemented(self):
        return '<p class="error">Sorry that report hasn\'t been implemented yet</p>' 
    
    @cached()
    def hh_surveys(self):
        """
        Get HH survey PI values
        """
        return self._not_implemented()
    
    @cached()
    def _fus(self):
        ret = []
        monthly_case_breakdown = self.report.case_list()
        for date in monthly_case_breakdown:
            for case_id in monthly_case_breakdown[date]:
                fu = CommCareCase.get_by_id(case_id)
                patient_guid = get_db().view("case/bhoma_case_lookup", 
                                             key=case_id, 
                                             reduce=False).one()["id"]
                pat = CPatient.get(patient_guid)
                fu.patient_id = pat.formatted_id
                fu.followup_attempted = followup_made(case_id)
                fu.followup_completed = successful_followup_made(fu)
                ret.append(fu)
                             
        return render_to_string("reports/partials/pis/chw/follow_ups.html", 
                                {"follow_ups": ret})
        
    @cached()
    def fu_att(self):
        # 2.Number of patient follow-ups attempted by CHW X by target date / total number of patient 
        # follow-ups assigned to CHW X older than the target date
        # Numerator: Number of followups in the denominator that have at least 1 FU form submitted
        # Denominator: Number of followups sent to the CHW within the report period
        return self._fus()
        
    @cached()
    def fu_complete(self):
        # 3. Number of patient follow-ups with outcomes recorded before it becomes lost to follow up / 
        # total number of patient follow-ups assigned to CHW X
        # Numerator: Follow-Ups with "bhoma_close" equal to "true" with "bhoma_outcome" 
        #            not equal to "lost_to_followup_time_window"
        # Denominator: Follow Ups assigned to CHW with due date in the report period
        
        return self._fus()
    
    @cached()
    def ref_turned_up(self):
        """
        Shows a list of the referral ids that were made and found.
        """
        made = get_referrals_made(self.chw, self.startdate, self.enddate)
        found = get_referrals_found(made.keys())
        all = [(r, r in found) for r in made]
        return render_to_string("reports/partials/pis/chw/referrals.html", 
                                {"referrals": all})
        
    @cached()
    def danger_sign_ref(self):
        # 6. Number of patients with danger signs referred from hh visit by CHW to clinic / 
        # Number of patients with danger signs on hh visit
        # Numerator: HH visits with danger signs and referred
        # Denominator: HH visits with danger signs
        return self._not_implemented()
        
        return ((date, _val(num, denom, "danger_sign_ref")) for \
                 date, (num, denom) in self.danger_sign_breakdown().items())
    
    def render_report(self):
        return getattr(self, self.slug)()
             

def get_chw_pi_report(chw, startdate, enddate):
    return ChwPiReport(chw, startdate, enddate).get_display_object()
    
