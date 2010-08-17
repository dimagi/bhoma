'''
Calculations having to do with pregnancy.
'''
from bhoma.apps.patient.encounters import config
from bhoma.utils.parsing import string_to_datetime
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.utils.couch import safe_index
from bhoma.apps.reports.calc.shared import get_hiv_result, is_first_visit,\
    tested_positive
from bhoma.apps.reports.models import CPregnancy

# TODO: maybe genericize this hard coded mess?

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
    
    def _first_visit_tested_positive(self):
        healthy_visits = [enc.get_xform() for enc in self.encounters if is_healthy_pregnency_encounter(enc)]
        healthy_visits = sorted(healthy_visits, key=lambda visit: visit.visit_number)
        
        for healthy_visit_data in healthy_visits:
            if tested_positive(healthy_visit_data):
                return healthy_visit_data
        
        return None
    
    def ever_tested_positive(self):
        for encounter in self.encounters:
            if tested_positive(encounter.get_xform()):
                return True
        return False
        
    def got_nvp_when_tested_positive(self):
        first_pos_visit = self._first_visit_tested_positive()
        pmtct = safe_index(first_pos_visit, ["pmtct"])
        if pmtct:  
            return "nvp" in pmtct
        return False

    
    def hiv_test_done(self):
        """Whether an HIV test was done at any point in the pregnancy"""
        for healthy_visit_data in [enc.get_xform() for enc in self.encounters if is_healthy_pregnency_encounter(enc)]:
            if safe_index(healthy_visit_data, ["hiv_first_visit", "hiv"]):
                return True
            elif safe_index(healthy_visit_data, ["hiv_after_first_visit", "hiv"]):
                return True
        return False
    
    def to_couch_object(self):
        return CPregnancy(patient_id = self.patient.get_id,
                          id = self.id,
                          lmp = self.lmp,
                          edd = self.edd,
                          visits = len(self.encounters),
                          first_visit_date = self.first_visit.visit_date,
                          ever_tested_positive = self.ever_tested_positive(),
                          got_nvp_when_tested_positive = self.got_nvp_when_tested_positive(),
                          hiv_test_done = self.hiv_test_done())
        
def is_healthy_pregnency_encounter(encounter):
    return encounter.get_xform().namespace == config.HEALTHY_PREGNANCY_NAMESPACE

def is_sick_pregnency_encounter(encounter):
    return encounter.get_xform().namespace == config.SICK_PREGNANCY_NAMESPACE

def is_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace in [config.HEALTHY_PREGNANCY_NAMESPACE, 
                                               config.SICK_PREGNANCY_NAMESPACE]

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
        # TODO, better aggregation.  right now we assume all is part of a single pregnancy
        return pregs[0]
    
    # second pass, find other visits and include them in the pregnancy
    if len(pregs) > 0:  
        for encounter in patient.encounters:
            if is_pregnancy_encounter(encounter) and not is_first_visit(encounter.get_xform()):
                matching_preg = get_matching_pregnancy(pregs, encounter)
                matching_preg.add_visit(encounter)
    
    
    return pregs