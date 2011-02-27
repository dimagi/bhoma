'''
All the custom hacks for bhoma-specific case logic
'''
from bhoma.apps.case import const
from bhoma.apps.case.models import CommCareCaseAction, CommCareCase
import logging
from bhoma.apps.xforms.models import CXFormInstance
from dimagi.utils.dates import safe_date_add
from bhoma.apps.patient.encounters import config
from bhoma.apps.patient.models.couch import CPatient
from couchdbkit.resource import ResourceNotFound

# A lot of what's currently in util.py should go here.

DAYS_AFTER_MISSED_APPOINTMENT_ACTIVE = 3 # how many days after a missed appointment do we tell the chw
DAYS_AFTER_MISSED_APPOINTMENT_DUE = 10   # how many days after a missed appointment is it due
DAYS_AFTER_PREGNANCY_ACTIVE_DUE = 5 # how many days after a pregnancy case becomes active is it due?

FOLLOW_TYPE_MAPPING = { const.FOLLOWUP_TYPE_REFER: const.PHONE_FOLLOWUP_TYPE_HOSPITAL,
                        const.FOLLOWUP_TYPE_FOLLOW_CLINIC: const.PHONE_FOLLOWUP_TYPE_MISSED_APPT }

def new_commcare_case(case_id, name, type, opened_on, modified_on, 
                      user_id, encounter_id, bhoma_case_id):
    # also make and add the CommCareCase
    # these are somewhat arbitraty
    # the external id is the bhoma case id.  also redundant since this is a child of that
    # create action
    external_id = bhoma_case_id
    create_action = CommCareCaseAction.new_create_action(opened_on)
    return CommCareCase(case_id=case_id, opened_on=opened_on, modified_on=modified_on, 
                 type=type, name=name, user_id=user_id, external_id=external_id, 
                 encounter_id=encounter_id, actions=[create_action,])
                        
def follow_type_from_form(value_from_form):
    if value_from_form in FOLLOW_TYPE_MAPPING: 
        return FOLLOW_TYPE_MAPPING[value_from_form]
    return "unknown"

def get_commcare_case_name(encounter, bhoma_case):
    return "%s|%s" % (encounter.type, bhoma_case.type) if bhoma_case.type else encounter.type

def get_user_id(encounter):
    return encounter.metadata.user_id if encounter.metadata else ""

def get_patient_id_from_form(form):
    return form.xpath("case/patient_id")
    
def get_latest_patient_id_format(id):
    if len(id) == 13:
        return id
    elif len(id) == 12:
        # 504180555555 -> 5040180555555
        return "%s0%s" % (id[:3], id[3:])
    else:
        logging.warning("unexpected id %s should be 12 or 13 digits")
        return id
    
def try_get_patient_id_from_referral(form):
    """
    The referrals might have a patient id or a referral id that we 
    can use to link the patient record.
    """
    if form.namespace == config.CHW_REFERRAL_NAMESPACE:
        bhoma_id = form.xpath("patient_id")
        if bhoma_id:
            str_id = jr_float_to_string_int(bhoma_id)
            str_id = get_latest_patient_id_format(str_id)
            try:
                pat = CPatient.view("patient/by_bhoma_id", key=str_id, reduce=False).one()
                if pat:
                    return pat.get_id
                else:
                    logging.warning("No patient found with bhoma id %s in referral form %s" % (str_id, form.get_id))
            except ResourceNotFound:
                logging.warning("No patient found with bhoma id %s in referral form %s" % (str_id, form.get_id))
                            
def get_bhoma_case_id_from_pregnancy(pregnancy):
    """
    Generate a unique (but deterministic) bhoma case id from pregnancy data.
    """
    return "preg%s" % CXFormInstance.get(pregnancy.anchor_form_id).sha1


def get_commcare_case_id_from_block(encounter, bhoma_case, case_block=None):
    """
    Generate a unique (but deterministic) case id from some case data.
    """
    if case_block and const.CASE_TAG_ID in case_block and case_block[const.CASE_TAG_ID]:
        return case_block[const.CASE_TAG_ID]
    return "%s-%s" % (bhoma_case.get_id, encounter.get_xform().sha1)

def get_bhoma_case_id_from_form(xformdoc):
    """
    Generate a unique (but deterministic) bhoma case id from the form generating it
    """
    # this is currently just the doc id and the checksum
    case_block = xformdoc.xpath(const.CASE_TAG)
    if case_block is not None and const.BHOMA_CASE_ID_TAG in case_block \
       and case_block[const.BHOMA_CASE_ID_TAG]:
        return case_block[const.BHOMA_CASE_ID_TAG]
    return "%s-%s" % (xformdoc.get_id, xformdoc.sha1)
    
def should_send_followup_to_phone(encounter):
    """
    Given an encounter object, whether there is urgency to send it to the phone
    Followups should only be sent to the phones if one of three
    conditions are met:
    - A severe symptom under assessment is selected
    - A danger sign is present
    - A followup visit scheduled at the clinic in < 5 days is missed.
    
    Returns a tuple object containing whether to send a followup and 
    (if so) why.  If no followup is sent the second argument is an 
    empty string.
    """
    
    def danger_sign_present(xform_doc):
        danger_signs = xform_doc.xpath("danger_signs")
        return danger_signs and danger_signs != "none" and danger_signs != "blank" 
    
    def urgent_clinic_followup(xform_doc):
        followup_type = xform_doc.xpath("case/followup_type")
        if const.FOLLOWUP_TYPE_FOLLOW_CLINIC == followup_type:
            try:
                follow_days = int(xform_doc.xpath("case/followup_date"))
                return follow_days < 5
            except ValueError:
                # we don't care if they didn't specify a date
                pass
        return False
        
    def severe_symptom_checked(xform_doc):
        assessment = xform_doc.xpath("assessment")
        if assessment:
            for key, val in assessment.items():
                if key != "categories" and val:
                    for subval in val.split(" "):
                        if subval.startswith("sev_"):
                            return True
        return False
    
    reasons = []
    if danger_sign_present(encounter.get_xform()):
        reasons.append("danger_sign_present")
    if severe_symptom_checked(encounter.get_xform()):
        reasons.append("severe_symptom_checked")
    if urgent_clinic_followup(encounter.get_xform()):
        reasons.append("urgent_clinic_followup")
    if reasons:
        return (True, " ".join(reasons))
    return (False, "sending_criteria_not_met")


def add_missed_appt_dates(cccase, appt_date):
    
    # active (and starts) 3 days after missed appointment
    # overdue 10 days after that
    # we create the cases immediately but they can be closed prior to 
    # ever being sent by an actual visit.
    cccase.missed_appointment_date = appt_date
    cccase.start_date = safe_date_add(appt_date, DAYS_AFTER_MISSED_APPOINTMENT_ACTIVE)
    cccase.activation_date = cccase.start_date
    cccase.due_date = safe_date_add(appt_date, DAYS_AFTER_MISSED_APPOINTMENT_DUE)
    
def jr_float_to_string_int(afloat):
    f = float(afloat)
    return "%d" % f