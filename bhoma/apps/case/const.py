
# how cases/referrals are tagged in the xform/couch
CASE_TAG = "case"
REFERRAL_TAG = "referral"
FOLLOWUP_TYPE_TAG = "followup_type"
OUTCOME_TAG = "outcome"
PATIENT_ID_TAG = "patient_id" 
BHOMA_CASE_ID_TAG = "bhoma_case_id"
FOLLOWUP_DATE_TAG = "followup_date"

# internal case identifiers
CASE_ACTION_CREATE = "create"
CASE_ACTION_UPDATE = "update"
CASE_ACTION_CLOSE = "close"
CASE_ACTIONS = (CASE_ACTION_CREATE, CASE_ACTION_UPDATE, CASE_ACTION_CLOSE)

CASE_TAG_TYPE = "case_type"
CASE_TAG_TYPE_ID = "case_type_id"
CASE_TAG_ID = "case_id"
CASE_TAG_NAME = "case_name"
CASE_TAG_MODIFIED = "date_modified"
CASE_TAG_USER_ID = "user_id"
CASE_TAG_EXTERNAL_ID = "external_id"
CASE_TAG_DATE_OPENED = "date_opened"
CASE_TAG_BHOMA_CLOSE = "bhoma_close"
CASE_TAG_BHOMA_OUTCOME = "bhoma_outcome"

CASE_TAGS = (CASE_ACTION_CREATE, CASE_ACTION_UPDATE, CASE_ACTION_CLOSE, REFERRAL_TAG, 
             CASE_TAG_TYPE_ID, CASE_TAG_ID, CASE_TAG_NAME, CASE_TAG_MODIFIED, CASE_TAG_USER_ID, 
             CASE_TAG_EXTERNAL_ID, CASE_TAG_DATE_OPENED ) 

CASE_TYPE_BHOMA_FOLLOWUP = "bhoma_followup"
CASE_TYPE_PREGNANCY = "pregnancy"

REFERRAL_ACTION_OPEN = "open"
REFERRAL_ACTION_UPDATE = "update"

REFERRAL_TAG_ID = "referral_id"
REFERRAL_TAG_FOLLOWUP_DATE = "followup_date"
REFERRAL_TAG_TYPE = "referral_type"
REFERRAL_TAG_TYPES = "referral_types"
REFERRAL_TAG_DATE_CLOSED = "date_closed"

FOLLOWUP_TYPE_REFER = "referral"
FOLLOWUP_TYPE_FOLLOW_CLINIC = "followup"
FOLLOWUP_TYPE_CLOSE = "case_closed"
FOLLOWUP_TYPE_NONE = "blank"
FOLLOWUP_TYPE_DEATH = "death"

PHONE_FOLLOWUP_TYPE_HOSPITAL = "hospital"
PHONE_FOLLOWUP_TYPE_CHW = "chw"
PHONE_FOLLOWUP_TYPE_MISSED_APPT = "missed_appt"
PHONE_FOLLOWUP_TYPE_PREGNANCY = "pregnancy"

OUTCOME_NONE = "no_outcome"
OUTCOME_MADE_APPOINTMENT = "made_appointment"
OUTCOME_RETURNED_TO_CLINIC = "returned_to_clinic"
OUTCOME_REFERRED_BACK_TO_CLINIC = "referred_back_to_clinic"
OUTCOME_ACTUALLY_WENT_TO_CLINIC = "actually_went_to_clinic"
OUTCOME_PENDING_PATIENT_MEETING = "pending_patient_meeting"

STATUS_RETURN_TO_CLINIC = "return to clinic"
STATUS_WENT_BACK_TO_CLINIC = "went back to clinic"
STATUS_PENDING_CHW_MEETING = "pending chw meeting"