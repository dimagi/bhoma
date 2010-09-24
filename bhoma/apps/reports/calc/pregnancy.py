'''
Calculations having to do with pregnancy.
'''
from datetime import timedelta
from bhoma.apps.patient.encounters import config
from bhoma.utils.parsing import string_to_datetime
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.apps.reports.calc.shared import get_hiv_result, is_first_visit,\
    tested_positive, encounter_in_range
from bhoma.apps.reports.models import PregnancyReportRecord
from bhoma.apps.encounter.models.couch import Encounter
import logging
from bhoma.apps.drugs.util import drug_type_prescribed


class Pregnancy(UnicodeMixIn):
    """
    Data that encapsulates a pregnancy.  We prepopulate all the data that needs to be 
    reported on here.
    """
    
    patient = None
    first_visit = None
    encounters = []
    
    def __init__(self, patient, id, lmp, edd, first_visit):
        self.patient = patient
        self.id = id
        self.lmp = lmp
        self.edd = edd
        self.first_visit = first_visit
        self.encounters = [first_visit]

    def __unicode__(self):
        return "%s, Pregancy: %s (due: %s)" % (self.patient.formatted_name, self.id, self.edd)
    
    
    @classmethod
    def from_first_visit(cls, patient, first_visit_enc):
        first_visit_form = first_visit_enc.get_xform()
        first_visit_data = first_visit_form.first_visit
        preg = Pregnancy(patient = patient,
                         id = first_visit_form.get_id,
                         lmp = string_to_datetime(first_visit_data["lmp"]).date(),
                         edd = string_to_datetime(first_visit_data["edd"]).date(), 
                         first_visit = first_visit_enc)
        return preg
                         
    def add_visit(self, visit_enc):
        # adds data from a visit
        self.encounters.append(visit_enc)
    
    def sorted_encounters(self):
        return sorted(self.encounters, key=lambda encounter: encounter.visit_date)
        
    def sorted_healthy_encounters(self):
        # TODO: should we sort by visit number or by date?
        return sorted([enc for enc in self.encounters if is_healthy_pregnancy_encounter(enc)], 
                      key=lambda encounter: encounter.visit_date)
        
    def sorted_sick_encounters(self):
        return sorted([enc for enc in self.encounters if is_sick_pregnancy_encounter(enc)], 
                      key=lambda encounter: encounter.visit_date)
        
    def _first_visit_tested_positive(self):
        healthy_visits = [enc.get_xform() for enc in self.sorted_healthy_encounters()]
        
        for healthy_visit_data in healthy_visits:
            if tested_positive(healthy_visit_data):
                return healthy_visit_data
        
        return None
    
    def pre_eclampsia_occurrences(self):
        
        def abnormal_preeclamp(xform):
            abnormal_bp = False
            bp = xform.xpath("blood_pressure")
            if bp:
                try:
                    systolic, diastolic = [int(val) for val in bp.split("/")]
                    abnormal_bp = systolic >= 140 or diastolic >= 90
                except ValueError:
                    logging.error("problem parsing blood pressure! %s, encounter %s" % (bp, encounter.get_id))
            
            gest_age = xform.xpath("gestational_age")
            return abnormal_bp and \
                   xform.xpath("urinalysis") == "protein_pos" and \
                   gest_age and int(gest_age) > 20
        
        def antihypertensive_prescribed(xform):
            # fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial");     
            return drug_type_prescribed(xform, "antihypertensive")
            
        # return a dictionary of encounters to either 1 (followed up correctly), 
        # or 0 (not followed up correctly).  Absence means there was no 
        # abnormal pre eclampsia
        to_return = {}
        
        for encounter in self.sorted_healthy_encounters():
            if abnormal_preeclamp(encounter.get_xform()) or \
               encounter.get_xform().found_in_multiselect_node("danger_signs", "oedema"):
                for sick_enc in self.sorted_sick_encounters():
                    if encounter_in_range(sick_enc, encounter.visit_date):
                        
                        if sick_enc.get_xform().xpath("resolution") == "referral" and \
                           antihypertensive_prescribed(sick_enc.get_xform()):
                            to_return[encounter] = 1
                        break
                if encounter not in to_return:
                    to_return[encounter] = 0

        return to_return
    
    def danger_signs_followed_up(self):
        """
        Proportion of visits filling out a Sick Pregnancy form with danger 
        signs present
        """
        # this one is going to emit a series of counts and dates.
        
        def has_danger_sign(xform):
            # i. Any Danger Sign apparent (vaginal bleeding, leaking fluid, contractions, pain urination, pelvic pressure, oedema/protein in urine) 
            if xform.xpath("danger_signs") != "none":
                return True
            # ii. A Breech Presentation after a Gestation Age of 27 weeks
            gest_age = xform.xpath("gestational_age")
            if gest_age:
                gest_age = int(gest_age)
                if gest_age > 27 and xform.xpath("presentation") == "breech":
                    return True
            # iii. No Fetal Heart Rate 
            if not xform.xpath("fetal_heart_rate"): 
                return True
            return False
        
        # return a dictionary of encounters to either 1 (followed up correctly), 
        # or 0 (not followed up correctly).  Absence means there were no 
        # danger signs.
        to_return = {}
        for encounter in self.sorted_healthy_encounters():
            if has_danger_sign(encounter.get_xform()):
                for sick_enc in self.sorted_sick_encounters():
                    if encounter_in_range(sick_enc, encounter.visit_date):
                        to_return[encounter] = 1
                        break
                if encounter not in to_return:
                    to_return[encounter] = 0
        return to_return
        
    def ever_tested_positive(self):
        for encounter in self.encounters:
            if tested_positive(encounter.get_xform()):
                return True
        return False
        
    def got_nvp_when_tested_positive(self):
        first_pos_visit = self._first_visit_tested_positive()
        if not first_pos_visit: return False
        
        pmtct = first_pos_visit.xpath("pmtct")
        if pmtct:  
            return "nvp" in pmtct
        return False

    def got_azt(self):
        for encounter in self.encounters:
            if encounter.get_xform().found_in_multiselect_node("pmtct", "azt"):
                return True
        return False

    def got_azt_on_consecutive_visits(self):
        prev_azt = False
        for encounter in self.sorted_healthy_encounters():
            curr_azt = encounter.get_xform().found_in_multiselect_node("pmtct", "azt")
            if curr_azt and prev_azt: return True
            prev_azt = curr_azt
        return False

        
    def hiv_test_done(self):
        """Whether an HIV test was done at any point in the pregnancy"""
        for healthy_visit_data in [enc.get_xform() for enc in self.encounters if is_healthy_pregnancy_encounter(enc)]:
            if healthy_visit_data.xpath("hiv_first_visit/hiv"):
                return True
            elif healthy_visit_data.xpath("hiv_after_first_visit/hiv"):
                return True
        return False
    
    def rpr_given_on_first_visit(self):
        rpr_node = self.first_visit.get_xform().xpath("rpr")
        return bool(rpr_node)
    
    def tested_positive_rpr(self):
        for enc in self.sorted_encounters():
            if enc.get_xform().xpath("rpr") == "r":
                return True
        return False
    
    def got_penicillin_when_rpr_positive(self):
        # NOTE: per visit or per pregnancy?  currently implemented per pregnancy
        rpr_postive = False
        for encounter in self.encounters:
            rpr_postive = rpr_postive or encounter.get_xform().xpath("rpr") ==  "r"
            if rpr_postive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "penicillin"):
                    return True
        return False
    
    def partner_got_penicillin_when_rpr_positive(self):
        # NOTE: per visit or per pregnancy?  currently implemented per pregnancy
        prev_rpr_postive = False
        for encounter in self.encounters:
            if prev_rpr_postive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "partner_penicillin"):
                    return True
            prev_rpr_postive = prev_rpr_postive or encounter.get_xform().xpath("rpr") == "r"
        return False
    
    
    def got_three_doses_fansidar(self):
        count = 0
        for encounter in self.encounters:
            if encounter.get_xform().found_in_multiselect_node("checklist", "fansidar"):
                count += 1
            if count >= 3: return True
        return False
    
    def to_couch_object(self):
        danger_sign_dict = self.danger_signs_followed_up()
        dates_danger_signs_followed = [enc.visit_date for enc, val in danger_sign_dict.items() if val == 1]
        dates_danger_signs_not_followed = [enc.visit_date for enc, val in danger_sign_dict.items() if val == 0]
        preeclamp_dict = self.pre_eclampsia_occurrences()
        dates_preeclamp_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 1]
        dates_preeclamp_not_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 0]
        return PregnancyReportRecord(patient_id = self.patient.get_id,
                          clinic_id = self.first_visit.metadata.clinic_id,
                          id = self.id,
                          lmp = self.lmp,
                          edd = self.edd,
                          visits = len(self.encounters),
                          first_visit_date = self.first_visit.visit_date,
                          ever_tested_positive = self.ever_tested_positive(),
                          got_nvp_when_tested_positive = self.got_nvp_when_tested_positive(),
                          hiv_test_done = self.hiv_test_done(), 
                          got_azt = self.got_azt(),
                          got_azt_on_consecutive_visits = self.got_azt_on_consecutive_visits(),
                          rpr_given_on_first_visit = self.rpr_given_on_first_visit(),
                          tested_positive_rpr = self.tested_positive_rpr(),
                          got_penicillin_when_rpr_positive = self.got_penicillin_when_rpr_positive(),
                          partner_got_penicillin_when_rpr_positive = self.partner_got_penicillin_when_rpr_positive(),
                          got_three_doses_fansidar = self.got_three_doses_fansidar(),
                          dates_danger_signs_followed = dates_danger_signs_followed,
                          dates_danger_signs_not_followed = dates_danger_signs_not_followed,
                          dates_preeclamp_treated = dates_preeclamp_treated,
                          dates_preeclamp_not_treated = dates_preeclamp_not_treated 
                          )
        
