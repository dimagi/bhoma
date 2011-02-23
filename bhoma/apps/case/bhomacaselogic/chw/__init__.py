from bhoma.apps.case.bhomacaselogic.chw.followup import process_followup
from bhoma.apps.patient.encounters import config
from bhoma.apps.case.bhomacaselogic.chw.referral import process_referral

def process_phone_form(patient, encounter):
    ns = encounter.get_xform().namespace 
    if ns == config.CHW_FOLLOWUP_NAMESPACE:
        process_followup(patient, encounter)
    elif ns == config.CHW_REFERRAL_NAMESPACE:
        process_referral(patient, encounter)