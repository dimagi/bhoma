from bhoma.apps.encounter.encounter import EncounterTypeRecord
from bhoma import const
import copy
import itertools

CLASSIFICATION_CLINIC = "clinic"
CLASSIFICATION_PHONE = "phone"

# eligibility functions
is_of_pregnancy_age = lambda x: x.age >= const.MIN_PREGNANCY_AGE and \
                                x.age <= const.MAX_PREGNANCY_AGE if x.age else True
is_under_five = lambda x: x.age <= 6 if x.age else True
is_over_five = lambda x: x.age >= 4 if x.age else True
meets_pregnancy_requirements = lambda x: x.gender == const.GENDER_FEMALE and \
                                         is_of_pregnancy_age(x)

GENERAL_VISIT_NAMESPACE = "http://cidrz.org/bhoma/general"
GENERAL_VISIT_SLUG      = "general"
GENERAL_VISIT_NAME      = "general visit"
GENERAL_VISIT_ENCOUNTER = EncounterTypeRecord(GENERAL_VISIT_SLUG, GENERAL_VISIT_NAMESPACE, GENERAL_VISIT_NAME, 
                                              classification=CLASSIFICATION_CLINIC, is_routine_visit=False, legality_func=is_over_five)


HEALTHY_PREGNANCY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy"
HEALTHY_PREGNANCY_SLUG      = "pregnancy"
HEALTHY_PREGNANCY_NAME      = "pregnancy"
HEALTHY_PREGNANCY_ENCOUNTER = EncounterTypeRecord(HEALTHY_PREGNANCY_SLUG, HEALTHY_PREGNANCY_NAMESPACE, HEALTHY_PREGNANCY_NAME, 
                                                  classification=CLASSIFICATION_CLINIC, is_routine_visit=True, legality_func=meets_pregnancy_requirements)

SICK_PREGNANCY_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy"
SICK_PREGNANCY_SLUG      = "sick_pregnancy"
SICK_PREGNANCY_NAME      = "sick pregnancy"
SICK_PREGNANCY_ENCOUNTER = EncounterTypeRecord(SICK_PREGNANCY_SLUG, SICK_PREGNANCY_NAMESPACE, SICK_PREGNANCY_NAME,
                                               classification=CLASSIFICATION_CLINIC, is_routine_visit=False, legality_func=meets_pregnancy_requirements)

UNDER_FIVE_NAMESPACE = "http://cidrz.org/bhoma/underfive"
UNDER_FIVE_SLUG      = "underfive"
UNDER_FIVE_NAME      = "under five"
UNDER_FIVE_ENCOUNTER = EncounterTypeRecord(UNDER_FIVE_SLUG, UNDER_FIVE_NAMESPACE, UNDER_FIVE_NAME, 
                                           classification=CLASSIFICATION_CLINIC, is_routine_visit=False, legality_func=is_under_five)

DELIVERY_NAMESPACE = "http://cidrz.org/bhoma/delivery"
DELIVERY_SLUG      = "delivery"
DELIVERY_NAME      = "delivery"
DELIVERY_ENCOUNTER = EncounterTypeRecord(DELIVERY_SLUG, DELIVERY_NAMESPACE, DELIVERY_NAME,
                                         classification=CLASSIFICATION_CLINIC, is_routine_visit=False, legality_func=meets_pregnancy_requirements)

CLINIC_ENCOUNTERS = {
    GENERAL_VISIT_SLUG:     GENERAL_VISIT_ENCOUNTER, 
    HEALTHY_PREGNANCY_SLUG: HEALTHY_PREGNANCY_ENCOUNTER, 
    SICK_PREGNANCY_SLUG:    SICK_PREGNANCY_ENCOUNTER,
    DELIVERY_SLUG:          DELIVERY_ENCOUNTER,  
    UNDER_FIVE_SLUG:        UNDER_FIVE_ENCOUNTER,
}

CHW_FOLLOWUP_NAMESPACE = "http://cidrz.org/bhoma/chw_followup"
CHW_REFERRAL_NAMESPACE = "http://cidrz.org/bhoma/new_clinic_referral"
CHW_HOUSEHOLD_SURVEY_NAMESPACE = "http://cidrz.org/bhoma/household_survey"
CHW_MONTHLY_SURVEY_NAMESPACE = "http://cidrz.org/bhoma/monthly_chw_survey"

def get_slug(xmlns):
    return xmlns.split("/")[-1]

def get_name(xmlns):
    return xmlns.split("/")[-1].replace("_", " ")

CHW_ENCOUNTERS = dict([(get_slug(xmlns), 
                        EncounterTypeRecord(get_slug(xmlns), xmlns, get_name(xmlns), CLASSIFICATION_PHONE)) \
                       for xmlns in (CHW_FOLLOWUP_NAMESPACE,
                                     CHW_REFERRAL_NAMESPACE,
                                     CHW_HOUSEHOLD_SURVEY_NAMESPACE,
                                     CHW_MONTHLY_SURVEY_NAMESPACE)])

# convenience/faster lookup of encounters by xmlns
ENCOUNTERS_BY_XMLNS = dict([(enc.namespace, enc) for enc in \
                            list(itertools.chain(CLINIC_ENCOUNTERS.values(), 
                                                 CHW_ENCOUNTERS.values()))])

def get_classification(xmlns):
    if xmlns in ENCOUNTERS_BY_XMLNS:
        return ENCOUNTERS_BY_XMLNS[xmlns].classification
    return "unknown"


def get_display_name(xmlns):
    if xmlns in ENCOUNTERS_BY_XMLNS:
        return ENCOUNTERS_BY_XMLNS[xmlns].name
    return xmlns

def get_encounters(patient):
    """
    Gets active encounters for a patient, based on their gender,
    age, pregnancy status, etc.
    Does this by setting the patient in the encounter and an is_active
    flag on the encounter.
    """
    to_return = {}
    for name, encounter in CLINIC_ENCOUNTERS.items():
        enc_copy = copy.copy(encounter)
        enc_copy.patient = patient
        enc_copy.is_active = enc_copy.is_active_for(patient)
        to_return[name] = enc_copy
    return to_return
