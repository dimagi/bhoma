'''
Calculations having to do with pregnancy.
'''
from datetime import timedelta
from bhoma.utils.parsing import string_to_datetime
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.apps.reports.calc.shared import get_hiv_result, tested_positive, encounter_in_range, not_on_haart 
from bhoma.apps.reports.models import PregnancyReportRecord
from bhoma.apps.encounter.models.couch import Encounter
import logging
from bhoma.apps.drugs.util import drug_type_prescribed
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_healthy_pregnancy_encounter,\
    is_sick_pregnancy_encounter
from bhoma.utils.couch import uid


class PregnancyReportData(UnicodeMixIn):
    """
    Data that encapsulates a pregnancy.  We prepopulate all the data that needs to be 
    reported on here.
    """
    
    patient = None
    _pregnancy = None
    
    def __init__(self, patient, pregnancy):
        self.patient = patient
        self._pregnancy = pregnancy
        self._id = uid.new()
        
    def __unicode__(self):
        return "%s, Pregancy: %s (due: %s)" % (self.patient.formatted_name, self.id, self.edd)
    
    
    def sorted_encounters(self):
        return self._pregnancy.sorted_encounters()
        
    def sorted_healthy_encounters(self):
        # TODO: should we sort by visit number or by date?
        return [enc for enc in self.sorted_encounters() if is_healthy_pregnancy_encounter(enc)]
        
    def sorted_sick_encounters(self):
        return [enc for enc in self.sorted_encounters() if is_sick_pregnancy_encounter(enc)]
    
    def get_first_healthy_visit(self):
        encs = self.sorted_healthy_encounters()
        if encs: 
            return encs[0]
        return None
    
    @property
    def get_id(self):
        return self._id
            
        
    def get_clinic_id(self):
        # TODO: this might not be right when patients start transferring or
        # being editable
        return self.patient.address.clinic_id
    

    def _first_visit_tested_positive_no_haart(self):
        healthy_visits = [enc.get_xform() for enc in self.sorted_healthy_encounters()]
        
        for healthy_visit_data in healthy_visits:
            if tested_positive(healthy_visit_data) and not_on_haart(healthy_visit_data):
                return healthy_visit_data
        
        return None
    
    def _first_visit_tested_positive_no_haart_ga_14(self):
        healthy_visits = [enc.get_xform() for enc in self.sorted_healthy_encounters()]
        
        for healthy_visit_data in healthy_visits:
            gest_age = healthy_visit_data.xpath("gestational_age") 
            if gest_age and int(gest_age) > 14 and \
            tested_positive(healthy_visit_data) and not_on_haart(healthy_visit_data):
                return healthy_visit_data
        
        return None
    
    def pre_eclampsia_occurrences(self):
        
        def abnormal_preeclamp_from_anc(xform):
            abnormal_bp = False
            bp = xform.xpath("blood_pressure")
            if bp:
                try:
                    systolic, diastolic = [int(val) for val in bp.split("/")]
                    abnormal_bp = systolic >= 160 or diastolic >= 110
                except ValueError:
                    logging.error("problem parsing blood pressure! %s, encounter %s" % (bp, encounter.get_id))
            
            gest_age = xform.xpath("gestational_age")
            protein_positive = xform.xpath("urinalysis") == "protein"
            
            return abnormal_bp and protein_positive and gest_age and int(gest_age) > 20
        
        def antihypertensive_prescribed(xform):
            # fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial");     
            return drug_type_prescribed(xform, "antihypertensive")
        
        def abnormal_preeclamp_from_sick(xform):
            abnormal_bp = False
            bp = xform.xpath("vitals/bp")
            if bp:
                try:
                    systolic, diastolic = [int(val) for val in bp.split("/")]
                    abnormal_bp = systolic >= 140 or diastolic >= 90
                except ValueError:
                    logging.error("problem parsing blood pressure! %s, encounter %s" % (bp, encounter.get_id))
            
            gest_age = xform.xpath("vitals/gest_age")
            
            severe_hypertension_symptom = False
            hypertension_symptoms = xform.xpath("assessment/hypertension")
            for symptom in hypertension_symptoms.split(" "):
                if symptom.startswith("sev_"):
                    severe_hypertension_symptom = True
                    
            return abnormal_bp and severe_hypertension_symptom and \
                gest_age and int(gest_age) > 20
                
        # return a dictionary of encounters to either 1 (followed up correctly), 
        # or 0 (not followed up correctly).  Absence means there was no 
        # abnormal pre eclampsia
        to_return = {}
        
        #get cases from healthy ANC form and assign mgmt outcome
        for encounter in self.sorted_healthy_encounters():
            if abnormal_preeclamp_from_anc(encounter.get_xform()):
                for sick_enc in self.sorted_sick_encounters():
                    if encounter_in_range(sick_enc, encounter.visit_date):
                        
                        if sick_enc.get_xform().xpath("resolution") == "referral" and \
                           antihypertensive_prescribed(sick_enc.get_xform()):
                            to_return[encounter] = 1
                        break
                if encounter not in to_return:
                    to_return[encounter] = 0
            #get cases from sick ANC form that may not be in healthy ANC form and assign outcome
            else:
                for sick_enc in self.sorted_sick_encounters():
                    if abnormal_preeclamp_from_sick(sick_enc.get_xform()) and \
                        (sick_enc.get_xform().found_in_multiselect_node("investigations/urine", "protein") or \
                        sick_enc.get_xform().found_in_multiselect_node("assessment/hypertension", "sev_urine") or \
                        sick_enc.get_xform().found_in_multiselect_node("assessment/hypertension", "mod_urine")):
                        for sick_enc in self.sorted_sick_encounters():
                            if encounter_in_range(sick_enc, encounter.visit_date):
                                
                                if sick_enc.get_xform().xpath("resolution") == "referral" and \
                                   antihypertensive_prescribed(sick_enc.get_xform()):
                                    to_return[encounter] = 1
                                break
                        if encounter not in to_return:
                            to_return[encounter] = 0
                    
        return to_return
      
    def ever_tested_positive(self):
        for encounter in self.sorted_encounters():
            if tested_positive(encounter.get_xform()):
                return True
        return False
    
    def not_on_haart_when_test_positive(self):
        first_pos_visit = self._first_visit_tested_positive_no_haart()
        if first_pos_visit: return True
        return False
            
    def got_nvp_when_tested_positive(self):
        first_pos_visit = self._first_visit_tested_positive_no_haart()
        if not first_pos_visit: return False
    
        pmtct = first_pos_visit.xpath("pmtct")
        if pmtct:  
            return "nvp" in pmtct
        return False

    
    def not_on_haart_when_test_positive_ga_14(self):
        first_pos_visit = self._first_visit_tested_positive_no_haart_ga_14()
        if first_pos_visit: return True


    def got_azt(self):
        for encounter in self.sorted_encounters():
            if encounter.get_xform().found_in_multiselect_node("pmtct", "azt"):
                return True
        return False
        
    def got_azt_when_tested_positive(self):
        first_pos_visit = self._first_visit_tested_positive_no_haart_ga_14()
        if not first_pos_visit: return False
        
        pmtct = first_pos_visit.xpath("pmtct")
        if pmtct:  
            return "azt" in pmtct
        return False

    def got_azt_haart_on_consecutive_visits(self):
        prev_azt_or_haart = False
        healthy_visits = [enc.get_xform() for enc in self.sorted_healthy_encounters()]
        for healthy_visit_data in healthy_visits:
            gest_age = healthy_visit_data.xpath("gestational_age")
            if gest_age and int(gest_age) > 14:
                curr_azt_or_haart = healthy_visit_data.found_in_multiselect_node("pmtct", "azt") or not not_on_haart(healthy_visit_data)            
                if curr_azt_or_haart and prev_azt_or_haart: return True
                prev_azt_or_haart = curr_azt_or_haart
        
    def hiv_test_done(self):
        """Whether an HIV test was done at any point in the pregnancy"""
        for healthy_visit_data in [enc.get_xform() for enc in self.sorted_healthy_encounters()]:
            if healthy_visit_data.xpath("hiv_first_visit/hiv"):
                return True
            elif healthy_visit_data.xpath("hiv_after_first_visit/hiv"):
                return True
        return False

    def rpr_given_on_first_visit(self):
        fv = self.get_first_healthy_visit()
        if fv:
            rpr_val = fv.get_xform().xpath("rpr") 
            return rpr_val == "nr"  or rpr_val == "r"
        return False

    
    def tested_positive_rpr(self):
        for enc in self.sorted_encounters():
            if enc.get_xform().xpath("rpr") == "r":
                return True
        return False
    
    def got_penicillin_when_rpr_positive(self):
        # NOTE: per visit or per pregnancy?  currently implemented per pregnancy
        for encounter in self.encounters:
            rpr_positive = rpr_positive or encounter.get_xform().xpath("rpr") ==  "r"
            if rpr_positive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "penicillin"):
                    return True
        return False
    
    def partner_got_penicillin_when_rpr_positive(self):
        # NOTE: per visit or per pregnancy?  currently implemented per pregnancy
        prev_rpr_positive = False
        for encounter in self.encounters:
            if prev_rpr_positive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "partner_penicillin"):
                    return True
            prev_rpr_positive = prev_rpr_positive or encounter.get_xform().xpath("rpr") == "r"
        return False
    
    
    def got_three_doses_fansidar(self):
        count = 0
        for encounter in self.sorted_encounters():
            if encounter.get_xform().found_in_multiselect_node("checklist", "fansidar"):
                count += 1
            if count >= 3: return True
        return False         
    
    def to_couch_object(self):
        preeclamp_dict = self.pre_eclampsia_occurrences()
        dates_preeclamp_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 1]
        dates_preeclamp_not_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 0]
        return PregnancyReportRecord(patient_id = self.patient.get_id,
                          clinic_id = self.get_clinic_id(),
                          id = self.get_id,
                          lmp = self._pregnancy.lmp if self._pregnancy.pregnancy_dates_set() else None,
                          edd = self._pregnancy.edd if self._pregnancy.pregnancy_dates_set() else None,
                          visits = len(self.sorted_encounters()),
                          first_visit_date = self._pregnancy.get_start_date(),
                          ever_tested_positive = self.ever_tested_positive(),
                          not_on_haart_when_test_positive = self.not_on_haart_when_test_positive(),
                          got_nvp_when_tested_positive = self.got_nvp_when_tested_positive(),
                          not_on_haart_when_test_positive_ga_14 = self.not_on_haart_when_test_positive_ga_14(),
                          got_azt_when_tested_positive = self.got_azt_when_tested_positive(),
                          got_azt_haart_on_consecutive_visits = self.got_azt_haart_on_consecutive_visits(),
                          rpr_given_on_first_visit = self.rpr_given_on_first_visit(),
                          tested_positive_rpr = self.tested_positive_rpr(),
                          got_penicillin_when_rpr_positive = self.got_penicillin_when_rpr_positive(),
                          partner_got_penicillin_when_rpr_positive = self.partner_got_penicillin_when_rpr_positive(),
                          got_three_doses_fansidar = self.got_three_doses_fansidar(),
                          dates_preeclamp_treated = dates_preeclamp_treated,
                          dates_preeclamp_not_treated = dates_preeclamp_not_treated )
        
