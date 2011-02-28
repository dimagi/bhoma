import logging
from dimagi.utils.couch.database import get_db

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
        <data key="ref_count">%(ref_count)s</data>
    </user_data>
</n0:registration>"""

def get_registration_xml(chw):
    # this doesn't feel like a final way to do this
    # all dates should be formatted like YYYY-MM-DD (e.g. 2010-07-28)
    referral_record = get_db().view("reports/chw_referral_ids",  
                            startkey=[chw.get_id],endkey=[chw.get_id, {}],
                            reduce=True).one()
    if referral_record and "value" in referral_record:
        last_ref = referral_record["value"]
        referral_count = int(last_ref[-4:])
    else:
        referral_count = 0
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
                                    "ref_count":referral_count,
                                    }

CASE_TEMPLATE = \
"""
<case>
    <case_id>%(case_id)s</case_id> 
    <date_modified>%(date_modified)s</date_modified>%(create_block)s%(update_block)s
</case>"""

CREATE_BLOCK = \
"""
    <create>%(base_data)s
    </create>"""

BASE_DATA = \
"""
        <case_type_id>%(case_type_id)s</case_type_id> 
        <user_id>%(user_id)s</user_id> 
        <case_name>%(case_name)s</case_name> 
        <external_id>%(external_id)s</external_id>"""

UPDATE_BLOCK = \
"""
    <update>%(update_base_data)s
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
    </update>"""

def date_to_xml_string(date):
        if date: return date.strftime("%Y-%m-%d")
        return ""
    
def get_case_xml(phone_case, create=True):
    if phone_case is None: 
        logging.error("Can't generate case xml for empty case!")
        return ""
    
    base_data = BASE_DATA % {"case_type_id": phone_case.case_type_id,
                             "user_id": phone_case.user_id,
                             "case_name": phone_case.case_name,
                             "external_id": phone_case.external_id }
    # if creating, the base data goes there, otherwise it goes in the
    # update block
    if create:
        create_block = CREATE_BLOCK % {"base_data": base_data }
        update_base_data = ""
    else:
        create_block = ""
        update_base_data = base_data
    
    update_block = UPDATE_BLOCK % { "update_base_data": update_base_data,
                                    "first_name": phone_case.first_name,
                                    "last_name": phone_case.last_name,
                                    "birth_date": date_to_xml_string(phone_case.birth_date),
                                    "birth_date_est": phone_case.birth_date_est, 
                                    "age": phone_case.age, 
                                    "sex": phone_case.sex,
                                    "village": phone_case.village,
                                    "contact": phone_case.contact,
                                    "bhoma_case_id": phone_case.bhoma_case_id,
                                    "bhoma_patient_id": phone_case.bhoma_patient_id,
                                    "followup_type": phone_case.followup_type,
                                    "orig_visit_type": phone_case.orig_visit_type,
                                    "orig_visit_diagnosis": phone_case.orig_visit_diagnosis,
                                    "orig_visit_date": date_to_xml_string(phone_case.orig_visit_date),
                                    "activation_date": date_to_xml_string(phone_case.activation_date),
                                    "due_date": date_to_xml_string(phone_case.due_date),
                                    "missed_appt_date": date_to_xml_string(phone_case.missed_appt_date),
                                  }
    return CASE_TEMPLATE % {"case_id": phone_case.case_id,
                            "date_modified": date_to_xml_string(phone_case.date_modified),
                            "create_block": create_block,
                            "update_block": update_block
                            } 
