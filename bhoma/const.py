
# installation types
LOCATION_TYPE_NATIONAL = "national"
LOCATION_TYPE_PROVINCE = "province"
LOCATION_TYPE_CLINIC   = "clinic"
LOCATION_TYPE_DISTRICT = "district"

# data attributes/properties
# this is used by the filter view
PROPERTY_CLINIC_ID = "clinic_id"

# TODO: should there be an encounter const file?
PROPERTY_ENCOUNTER_DATE = "encounter_date"

# couch constants

# views
VIEW_ALL_PATIENTS = "patient/all"
VIEW_PATIENT_SEARCH = "patient/search"
VIEW_PATIENT_BY_LAST_NAME = "patient/by_last_name"

# filters
FILTER_CLINIC = "patient/clinic"
FILTER_DISTRICT = "patient/district"
FILTER_XFORMS = "xforms/xforms"
FILTER_CONFLICTING_PATIENTS = "patient/conflicts"
FILTER_PATIENTS = "patient/patients"

# forms stuff
MIN_PREGNANCY_AGE = 10
MAX_PREGNANCY_AGE = 55
GENDER_MALE = "m"
GENDER_FEMALE = "f"
GENDERS = ((GENDER_MALE, "male"), 
           (GENDER_FEMALE, "female"))

SERVER_TIMESTAMP_TAG = "bhoma_server_timestamp"

