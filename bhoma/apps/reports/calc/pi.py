from collections import defaultdict
from bhoma.apps.reports.shortcuts import get_monthly_submission_breakdown
from bhoma.apps.patient.encounters import config
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay, FractionalDisplayValue, CHWPIReportDisplayRow
from django.utils.datastructures import SortedDict
from bhoma.apps.zones.models import ClinicZone
import itertools
from bhoma.apps.reports.calc.chw import get_monthly_referral_breakdown,\
    get_monthly_case_breakdown, get_monthly_fu_breakdown,\
    get_monthly_danger_sign_referred_breakdown
from bhoma.apps.reports import const


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
        return get_monthly_submission_breakdown\
                    (self.chw_id, config.CHW_FOLLOWUP_NAMESPACE, 
                     self.startdate, self.enddate)
        
    @cached()
    def hh_submission_breakdown(self):
        return get_monthly_submission_breakdown\
                (self.chw_id, config.CHW_HOUSEHOLD_SURVEY_NAMESPACE, 
                 self.startdate, self.enddate)
    @cached()
    def referral_submission_breakdown(self):
        return get_monthly_submission_breakdown\
                    (self.chw_id, config.CHW_REFERRAL_NAMESPACE, 
                     self.startdate, self.enddate)
    
    @cached()
    def case_breakdown(self):
        return get_monthly_case_breakdown(self.chw, self.startdate, 
                                          self.enddate)
            
    
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
        # Numerator: Follow Up forms filled out
        # Denominator: Follow Ups assigned to CHW with due date in the report period
        
        ret = []
        for date in self.fu_dates():
            fu_got = self.case_breakdown()[date] 
            fu_made = self.fu_submission_breakdown()[date]
            value_display = _val(fu_made, fu_got, "fu_att")
            ret.append((date, value_display))
        
        return ret
    
    @cached()
    def fu_complete(self):
        # 3. Number of patient follow-ups with outcomes recorded before it becomes lost to follow up / 
        # total number of patient follow-ups assigned to CHW X
        # Numerator: Follow-Ups with "bhoma_close" equal to "true" with "bhoma_outcome" 
        #            not equal to "lost_to_followup_time_window"
        # Denominator: Follow Ups assigned to CHW with due date in the report period
        ret = []
        for date in self.fu_dates():
            fu_got = self.case_breakdown()[date]
            fu_breakdown_month_success = self.fu_breakdown()[date][True]
            success_fu_count = sum(val for key, val in \
                                   fu_breakdown_month_success.items() \
                                   if key != "lost_to_followup_time_window")
            value_display = _val(success_fu_count, fu_got, "fu_complete")
            ret.append((date, value_display))
        return ret
    
    @cached()
    def ref_turned_up(self):
        # 4.  Total number of referrals that turn up at the clinic / Total Number of Referrals made by each CHW
        # Numerator: Visits with a matching referral ID
        # Denominator: Referrals
        ret = []
        for date, count in self.referral_submission_breakdown().items():
            ref_found = self.referral_breakdown()[date]
            value_display = _val(ref_found, count, "ref_turned_up")
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
        """
        return getattr(self, slug)()
        

def get_chw_pi_report(chw, startdate, enddate):
    
    return ChwPiReport(chw, startdate, enddate).get_display_object()
    
    
    