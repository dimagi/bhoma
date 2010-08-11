'''
Calculations having to do with pregnancy.
'''
from bhoma.apps.patient.encounters import config
from bhoma.utils.parsing import string_to_datetime
from bhoma.utils.mixins import UnicodeMixIn

# TODO: maybe genericize this hard coded mess?

class Pregnancy(UnicodeMixIn):
    """
    Data that encapsulates a pregnancy
    """
    
    patient = None
    encounters = []
    
    def __init__(self, patient, lmp, edd):
        self.patient = patient
        self.lmp = lmp
        self.edd = edd

    def __unicode__(self):
        return "%s (due: %s)" % (self.patient.formatted_name, self.edd)
    
    @classmethod
    def from_first_visit(cls, patient, first_visit):
        return Pregnancy(patient = patient,
                         lmp = string_to_datetime(first_visit["lmp"]).date(),
                         edd = string_to_datetime(first_visit["edd"]).date())
                         
                         

def is_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace in [config.HEALTHY_PREGNANCY_NAMESPACE, config.SICK_PREGNANCY_NAMESPACE]

def extract_pregnancies(patient):
    """
    From a patient object, extract a list of pregnancies.
    """
    
    pregs = []
    is_first_visit = lambda form:  hasattr(form, "first_visit")
    # first pass, find pregnancy first visits and create pregnancy for them
    for encounter in patient.encounters:
        if encounter.type == config.HEALTHY_PREGNANCY_NAME and is_first_visit(encounter.get_xform()):
            pregs.append(Pregnancy.from_first_visit(patient, encounter.get_xform().first_visit))

    # second pass, find other visits and include them in the pregnancy
    if len(pregs) > 0:  
        for encounter in patient.encounters:
            if is_pregnancy_encounter(encounter) and not is_first_visit(encounter.get_xform()):
                # TODO, better aggregation.  right now we assume all is part of a single pregnancy
                matching_preg = pregs[0]
                matching_preg.encounters.append(encounter)
    
    return pregs