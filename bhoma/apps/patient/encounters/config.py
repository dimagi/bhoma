from bhoma.apps.encounter.encounter import EncounterTypeRecord
from bhoma import const
import copy

CHW_FOLLOWUP_NAMESPACE = "http://cidrz.org/bhoma/chw_followup"
    
# fake
REGISTRATION_NAMESPACE = "http://cidrz.org/bhoma/registration"
REGISTRATION_SLUG      = "registration"
REGISTRATION_NAME      = "registration"
REGISTRATION_ENCOUNTER = EncounterTypeRecord(REGISTRATION_NAME, REGISTRATION_NAMESPACE, REGISTRATION_NAME)

# eligibility functions
is_under_five = lambda x: x.age <= 5
is_over_five = lambda x: x.age >= 5
meets_pregnancy_requirements = lambda x: x.age >= const.MIN_PREGNANCY_AGE and x.gender == const.GENDER_FEMALE

# real

GENERAL_VISIT_NAMESPACE = "http://cidrz.org/bhoma/general"
GENERAL_VISIT_SLUG      = "general_visit"
GENERAL_VISIT_NAME      = "general visit"
GENERAL_VISIT_ENCOUNTER = EncounterTypeRecord(GENERAL_VISIT_NAME, GENERAL_VISIT_NAMESPACE, GENERAL_VISIT_NAME, 
                                              is_routine_visit=False, legality_func=is_over_five)


HEALTHY_PREGNANCY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy"
HEALTHY_PREGNANCY_SLUG      = "healthy_pregnancy"
HEALTHY_PREGNANCY_NAME      = "healthy pregnancy"
HEALTHY_PREGNANCY_ENCOUNTER = EncounterTypeRecord(HEALTHY_PREGNANCY_NAME, HEALTHY_PREGNANCY_NAMESPACE, HEALTHY_PREGNANCY_NAME, 
                                                  is_routine_visit=True, legality_func=meets_pregnancy_requirements)

SICK_PREGNANCY_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy"
SICK_PREGNANCY_SLUG      = "sick_pregnancy"
SICK_PREGNANCY_NAME      = "sick pregnancy"
SICK_PREGNANCY_ENCOUNTER = EncounterTypeRecord(SICK_PREGNANCY_NAME, SICK_PREGNANCY_NAMESPACE, SICK_PREGNANCY_NAME,
                                               is_routine_visit=False, legality_func=meets_pregnancy_requirements)

UNDER_FIVE_NAMESPACE = "http://cidrz.org/bhoma/underfive"
UNDER_FIVE_SLUG      = "under_five"
UNDER_FIVE_NAME      = "under five"
UNDER_FIVE_ENCOUNTER = EncounterTypeRecord(UNDER_FIVE_NAME, UNDER_FIVE_NAMESPACE, UNDER_FIVE_NAME, 
                                           is_routine_visit=False, legality_func=is_under_five)

DELIVERY_NAMESPACE = "http://cidrz.org/bhoma/delivery"
DELIVERY_SLUG      = "delivery"
DELIVERY_NAME      = "delivery"
DELIVERY_ENCOUNTER = EncounterTypeRecord(DELIVERY_NAME, DELIVERY_NAMESPACE, DELIVERY_NAME,
                                         is_routine_visit=False, legality_func=meets_pregnancy_requirements)

ACTIVE_ENCOUNTERS = {
    GENERAL_VISIT_SLUG:     GENERAL_VISIT_ENCOUNTER, 
    HEALTHY_PREGNANCY_SLUG: HEALTHY_PREGNANCY_ENCOUNTER, 
    SICK_PREGNANCY_SLUG:    SICK_PREGNANCY_ENCOUNTER,
    DELIVERY_SLUG:          DELIVERY_ENCOUNTER,  
    UNDER_FIVE_SLUG:        UNDER_FIVE_ENCOUNTER,
}

ACTIVE_ENCOUNTERS_FEMALE = {
    GENERAL_VISIT_SLUG:     GENERAL_VISIT_ENCOUNTER, 
    HEALTHY_PREGNANCY_SLUG: HEALTHY_PREGNANCY_ENCOUNTER, 
    SICK_PREGNANCY_SLUG:    SICK_PREGNANCY_ENCOUNTER,
    DELIVERY_SLUG:          DELIVERY_ENCOUNTER,  
    UNDER_FIVE_SLUG:        UNDER_FIVE_ENCOUNTER, 
}

ACTIVE_ENCOUNTERS_MALE = {
    GENERAL_VISIT_SLUG:     GENERAL_VISIT_ENCOUNTER, 
    UNDER_FIVE_SLUG:        UNDER_FIVE_ENCOUNTER, 
}

def get_encounters(patient):
    """
    Gets active encounters for a patient, based on their gender,
    age, pregnancy status, etc.
    Does this by setting the patient in the encounter and an is_active
    flag on the encounter.
    """
    to_return = {}
    for name, encounter in ACTIVE_ENCOUNTERS.items():
        enc_copy = copy.copy(encounter)
        enc_copy.patient = patient
        enc_copy.is_active = enc_copy.is_active_for(patient)
        to_return[name] = enc_copy
    return to_return
