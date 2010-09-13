import logging
from bhoma.apps.case import const
from datetime import datetime
from bhoma.utils.couch import safe_index
from bhoma.apps.phone import phonehacks

RESTOREDATA_TEMPLATE =\
"""<?xml version='1.0' encoding='UTF-8'?>
<restoredata>
<restore_id>%(restore_id)s</restore_id>%(registration)s%(case_list)s
</restoredata>
"""

# Response template according to 
# http://code.dimagi.com/JavaRosa/wiki/ServerResponseFormat

RESPONSE_TEMPLATE = \
"""<?xml version='1.0' encoding='UTF-8'?>
<OpenRosaResponse>
    <OpenRosaStatusCode>%(status_code)s</OpenRosaStatusCode>
    <SubmissionStatusCode>%(submit_code)s</SubmissionStatusCode>
    <SubmissionId>%(id)s</SubmissionId>
    <FormsSubmittedToday>%(forms_today)s</FormsSubmittedToday>
    <TotalFormsSubmitted>%(total_forms)s</TotalFormsSubmitted>
</OpenRosaResponse>"""

def get_response(xform_doc, forms_today=1, total_forms=1):
    # TODO: implement 
    return RESPONSE_TEMPLATE % {"status_code": 2000,
                                "submit_code": 200,
                                "id": xform_doc.get_id,
                                "forms_today": forms_today,
                                "total_forms": total_forms
                                }

REGISTRATION_TEMPLATE = \
"""
<n0:registration xmlns:n0="http://openrosa.org/user-registration">
    <username>%(username)s</username>
    <password>%(password)s</password>
    <uuid>%(uuid)s</uuid>
    <date>%(date)s</date>
    <user_data>
        <data key="firstname">%(firstname)s</data>
        <data key="lastname">%(lastname)s</data>
        <data key="sex">%(gender)s</data>
        <data key="clinic_id">%(clinic_id)s</data>
        <data key="clinic_prefix">%(clinic_prefix)s</data>
        <data key="chw_zone">%(chw_zone)s</data>
    </user_data>
</n0:registration>"""

def get_registration_xml(chw):
    # TODO: this doesn't feel like a final way to do this
    
    # all dates should be formatted like YYYY-MM-DD (e.g. 2010-07-28)
    return REGISTRATION_TEMPLATE % {"username": chw.username,
                                    "password": chw.password,
                                    "uuid":     chw.get_id,
                                    "date":     chw.created_on.strftime("%Y-%m-%d"),
                                    "firstname":chw.first_name,
                                    "lastname": chw.last_name,
                                    "gender":   chw.gender,
                                    "clinic_id":chw.current_clinic_id,
                                    "clinic_prefix": chw.current_clinic_id[2] + chw.current_clinic_id[4:6],
                                    "chw_zone": chw.current_clinic_zone,
                                    }

CASE_TEMPLATE = \
"""
<case>
    <case_id>%(case_id)s</case_id> 
    <date_modified>%(date_modified)s</date_modified> 
    <create>
        <case_type_id>%(case_type_id)s</case_type_id> 
        <user_id>%(user_id)s</user_id> 
        <case_name>%(case_name)s</case_name> 
        <external_id>%(external_id)s</external_id> 
    </create> 
    <update> 
        <first_name>%(first_name)s</first_name>
        <last_name>%(last_name)s</last_name>
        <birth_date>%(birth_date)s</birth_date>
        <birth_date_est>%(birth_date_est)s</birth_date_est>
        <age>%(age)s</age>
        <sex>%(sex)s</sex>
        <village>%(village)s</village>
        <contact>%(contact)s</contact>
        <bhoma_case_id>%(bhoma_case_id)s</bhoma_case_id>
        <bhoma_patient_id>%(bhoma_patient_id)s</bhoma_patient_id>
        <followup_type>%(followup_type)s</followup_type>
        <orig_visit_type>%(orig_visit_type)s</orig_visit_type>
        <orig_visit_diagnosis>%(orig_visit_diagnosis)s</orig_visit_diagnosis>
        <orig_visit_date>%(orig_visit_date)s</orig_visit_date>
        <activation_date>%(activation_date)s</activation_date>
        <due_date>%(due_date)s</due_date>
        <missed_appt_date>%(missed_appt_date)s</missed_appt_date>
        <ttl_missed_apts>%(ttl_missed_apts)s</ttl_missed_apts> 
        <current_followup_status>%(current_followup_status)s</current_followup_status>
    </update> 
</case>"""

def get_case_xml(case):
    
    if not case.patient:
        logging.error("No patient found found inside %s, will not be downloaded to phone" % case)
        return ""
    
    # complicated logic, but basically a case is open based on the conditions 
    # below which amount to it not being closed, and if it has a start date, 
    # that start date being before or up to today
    open_inner_cases = [cinner for cinner in case.commcare_cases \
                        if not cinner.closed and cinner.is_started()]
                           
    if len(open_inner_cases) == 0:
        logging.warning("No open case found inside %s, will not be downloaded to phone" % case)
        return ""
    elif len(open_inner_cases) > 1:
        logging.error("More than one open case found inside %s.  Only the most recent will not be downloaded to phone" % case)
        ccase = sorted(open_inner_cases, key=lambda case: case.opened_on)[0]
    else:
        ccase = open_inner_cases[0]
    
    
    def date_to_string(date):
        if date: return date.strftime("%Y-%m-%d")
        return ""
        
    # this currently dumps everything in a single update block
    # TODO: this doesn't feel like a final way to do this
    return CASE_TEMPLATE % {"case_id": ccase._id,
                            "date_modified": date_to_string(case.modified_on),
                            "case_type_id": const.CASE_TYPE_BHOMA_FOLLOWUP,
                            "user_id": ccase.user_id,
                            "case_name": ccase.name,
                            "external_id": ccase.external_id,
                            "first_name": case.patient.first_name,
                            "last_name": case.patient.last_name,
                            "birth_date": date_to_string(case.patient.birthdate),
                            "birth_date_est": case.patient.birthdate_estimated, #  (maybe?)
                            "age": case.patient.age, #  (preformatted age string) (maybe?)
                            "sex": case.patient.gender,
                            "village": case.patient.address.village,
                            "contact": case.patient.default_phone,
                            "bhoma_case_id": ccase.external_id, # TODO: remove? duplicate with external_id
                            "bhoma_patient_id": case.patient.get_id, # (maybe?) is this meant to be internal or external?
                            
                            "followup_type": phonehacks.followup_type_transform(ccase.followup_type), # (post-hospital, missed appt, chw followup, etc.)
                            "orig_visit_type": phonehacks.original_visit_type_transform(case.get_encounter().type), # (general, under-5, etc.)
                            "orig_visit_diagnosis": case.type,
                            "orig_visit_date": date_to_string(case.get_encounter().visit_date),
                            "activation_date": date_to_string(ccase.activation_date), # TODO (don't followup before this date) 
                            "due_date": date_to_string(ccase.due_date), #  (followup by this date)
                            
                            "missed_appt_date": date_to_string(safe_index(ccase, ["missed_appointment_date",])), 
                            "ttl_missed_apts": 1,# TODO total number of missed appts in this current case or # attempts CHW has made to get them back to the clinic -- not really important, but could be useful to know) (maybe?) 
                            
                            "current_followup_status": "new" # TODO  (maybe?)
                            } 
