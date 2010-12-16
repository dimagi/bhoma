'''
Calculations having to do with pregnancy.
'''
from datetime import timedelta
from bhoma.apps.patient.encounters import config
from bhoma.utils.parsing import string_to_datetime
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.apps.reports.calc.shared import get_hiv_result, is_first_visit,\
    tested_positive, encounter_in_range, not_on_haart
from bhoma.apps.reports.models import CPregnancy
from bhoma.apps.encounter.models.couch import Encounter
import logging
from bhoma.apps.drugs.util import drug_type_prescribed

"""Any form before EDD + this many days counts for that pregnancy."""
PAST_DELIVERY_MATCH_CUTOFF = 60

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
        
    def sorted_delivery_encounters(self):
        return sorted([enc for enc in self.encounters if is_delivery_encounter(enc)], 
                      key=lambda encounter: encounter.visit_date)
        
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
            protein_positive = xform.xpath("urinalysis_protein") == "p"
            
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
        for encounter in self.encounters:
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
        for encounter in self.sorted_healthy_encounters():
            gest_age = encounter.xpath("vitals/gest_age")
            if gest_age and int(gest_age) > 14:
                curr_azt_or_haart = encounter.get_xform().found_in_multiselect_node("pmtct", "azt") or not not_on_haart(encounter.get_xform())            
                if curr_azt_or_haart and prev_azt_or_haart: return True
                prev_azt_or_haart = curr_azt_or_haart
        return False

    def rpr_given_on_first_visit(self):
        if self.first_visit.get_xform().xpath("rpr") == "nr" or "r":
            return True
        return False
    
    def tested_positive_rpr(self):
        for enc in self.sorted_encounters():
            if enc.get_xform().xpath("rpr") == "r":
                return True
        return False
    
    def got_penicillin_when_rpr_positive(self):
        # currently implemented per pregnancy
        rpr_positive = False
        for encounter in self.encounters:
            rpr_positive = rpr_positive or encounter.get_xform().xpath("rpr") ==  "r"
            if rpr_positive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "penicillin"):
                    return True
        return False
    
    def partner_got_penicillin_when_rpr_positive(self):
        # currently implemented per pregnancy
        prev_rpr_positive = False
        for encounter in self.encounters:
            if prev_rpr_positive:
                if encounter.get_xform().found_in_multiselect_node("checklist", "partner_penicillin"):
                    return True
            prev_rpr_positive = prev_rpr_positive or encounter.get_xform().xpath("rpr") == "r"
        return False
    
    
    def got_three_doses_fansidar(self):
        count = 0
        for encounter in self.encounters:
            if encounter.get_xform().found_in_multiselect_node("checklist", "fansidar"):
                count += 1
            if count >= 3: return True
        return False         
    
    def to_couch_object(self):
        preeclamp_dict = self.pre_eclampsia_occurrences()
        dates_preeclamp_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 1]
        dates_preeclamp_not_treated = [enc.visit_date for enc, val in preeclamp_dict.items() if val == 0]
        return CPregnancy(patient_id = self.patient.get_id,
                          clinic_id = self.first_visit.metadata.clinic_id,
                          id = self.id,
                          lmp = self.lmp,
                          edd = self.edd,
                          visits = len(self.encounters),
                          first_visit_date = self.first_visit.visit_date,
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
                          dates_preeclamp_not_treated = dates_preeclamp_not_treated 
                          )
        
def is_healthy_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace == config.HEALTHY_PREGNANCY_NAMESPACE

def is_sick_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace == config.SICK_PREGNANCY_NAMESPACE

def is_delivery_encounter(encounter):
    return encounter.get_xform().namespace == config.DELIVERY_NAMESPACE

def is_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace in [config.HEALTHY_PREGNANCY_NAMESPACE, 
                                               config.SICK_PREGNANCY_NAMESPACE,
                                               config.DELIVERY_NAMESPACE]

def extract_pregnancies(patient):
    """
    From a patient object, extract a list of pregnancies.
    """
    
    pregs = []
    
    # first pass, find pregnancy first visits and create pregnancy for them
    for encounter in patient.encounters:
        form = encounter.get_xform()
        if encounter.type == config.HEALTHY_PREGNANCY_NAME and is_first_visit(form):
            pregs.append(Pregnancy.from_first_visit(patient, encounter))
    
    def get_matching_pregnancy(pregs, encounter):
        
        sorted_pregs = sorted(pregs, key=lambda preg: preg.first_visit.visit_date)
        
        for preg in sorted_pregs:
            cutoff = preg.edd + timedelta(days=PAST_DELIVERY_MATCH_CUTOFF)
            if preg.first_visit.visit_date <= encounter.visit_date <= cutoff:
                return preg
        logging.error("no matching pregnancy found for good candidate match!  Encounter id: %s" % encounter.get_xform().get_id)
        
        # find the most recent one before the visit
        candidate_preg = None
        for preg in sorted_pregs:
            if preg.first_visit.visit_date <= encounter.visit_date:
                candidate_preg = preg
            else:
                break
        if candidate_preg: return candidate_preg
        
        # super fail - this is before any pregnancy we know about. 
        logging.error("no matching pregnancy found before current date!  Encounter id: %s" % encounter.get_xform().get_id)
        return sorted_pregs[0]
    
    # second pass, find other visits and include them in the pregnancy
    if len(pregs) > 0:  
        for encounter in patient.encounters:
            if is_pregnancy_encounter(encounter) and not is_first_visit(encounter.get_xform()):
                matching_preg = get_matching_pregnancy(pregs, encounter)
                matching_preg.add_visit(encounter)
    
    
    return pregs