'''
All the custom hacks for bhoma-specific case logic
'''
from bhoma.apps.case import const
from datetime import timedelta
from bhoma.apps.case.models.couch import CommCareCaseAction, CommCareCase

# A lot of what's currently in util.py should go here.

DAYS_AFTER_REFERRAL_CHECK = 14 # when a hospital referral is made, when checkup happens
DAYS_BEFORE_FOLLOW_ACTIVE = 2  # when something is on a date - how many days before it is active
DAYS_AFTER_FOLLOW_DUE = 5      # when something is on a date - how many days after it is due
DAYS_AFTER_MISSED_APPOINTMENT_ACTIVE = 3 # how many days after a missed appointment do we tell the chw
DAYS_AFTER_MISSED_APPOINTMENT_DUE = 10   # how many days after a missed appointment is it due

FOLLOW_TYPE_MAPPING = { const.FOLLOWUP_TYPE_REFER: const.PHONE_FOLLOWUP_TYPE_HOSPITAL,
                        const.FOLLOWUP_TYPE_FOLLOW_CHW: const.PHONE_FOLLOWUP_TYPE_CHW,
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


def add_missed_appt_dates(cccase, appt_date):
    
    # active (and starts) 3 days after missed appointment
    # due 7 days after that
    # we create the cases immediately but they can be closed prior to 
    # ever being sent by an actual visit.
    cccase.missed_appointment_date = appt_date
    cccase.start_date = (appt_date + timedelta(days=DAYS_AFTER_MISSED_APPOINTMENT_ACTIVE)).date()
    cccase.activation_date = cccase.start_date
    cccase.due_date = (appt_date + timedelta(DAYS_AFTER_MISSED_APPOINTMENT_DUE)).date()