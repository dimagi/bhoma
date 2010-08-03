
RESTOREDATA_TEMPLATE =\
"""<restoredata>
%(inner)s
</restoredata>
"""
import logging
from bhoma.apps.case import const

REGISTRATION_TEMPLATE = \
"""<n0:registration xmlns:n0="http://openrosa.org/user-registration">
    <username>%(username)s</username>
    <password>%(password)s</password>
    <uuid>%(uuid)s</uuid>
    <date>%(date)s</date>
    <user_data>
        <data key="firstname">%(firstname)s</data>
        <data key="lastname">%(lastname)s</data>
        <data key="sex">%(gender)s</data>
        <data key="clinic_id">%(clinic_id)s</data>
    </user_data>
</n0:registration>"""

def get_registration_xml(chw):
    # TODO: this doesn't feel like a final way to do this
    # date should be formatted like 2010-07-28
    return REGISTRATION_TEMPLATE % {"username": chw.username,
                                    "password": chw.password,
                                    "uuid":     chw.get_id,
                                    "date":     chw.created_on.strftime("%Y-%m-%d"),
                                    "firstname":chw.first_name,
                                    "lastname": chw.last_name,
                                    "gender":   chw.gender,
                                    "clinic_id":chw.current_clinic_id}

CASE_TEMPLATE = \
"""<case>
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
        <birth_date_est>%(birth_date_est)s</birth_date_est> (maybe?)
        <age>%(age)s</age> (preformatted age string) (maybe?)
        <sex>%(sex)s</sex>
        <village>%(village)s</village>
        <contact>%(contact)s</contact> (phone #)
        <bhoma_case_id>%(bhoma_case_id)s</bhoma_case_id>
        <bhoma_patient_id>%(bhoma_patient_id)s</bhoma_patient_id> (maybe?)

        <followup_type>%(followup_type)s</followup_type> (post-hospital, missed appt, chw followup, etc.)
        <orig_visit_type>%(orig_visit_type)s</orig_visit_type> (general, under-5, etc.)
        <orig_visit_diagnosis>%(orig_visit_diagnosis)s</orig_visit_diagnosis>
        <orig_visit_date>%(orig_visit_date)s</orig_visit_date>

        <activation_date>%(activation_date)s</activation_date> (don't followup before this date)
        <due_date>%(due_date)s</due_date> <!--(followup by this date)-->

        <missed_appt_date>%(missed_appt_date)s</missed_appt_date>
        <ttl_missed_apts>%(ttl_missed_apts)s</ttl_missed_apts> <!--total number of missed appts in this current case or # attempts CHW has made to get them back to the clinic -- not really important, but could be useful to know) (maybe?)-->

        <current_followup_status>%(current_followup_status)s</current_followup_status> <!--maybe?-->
    </update> 
</case>"""

def get_case_xml(case):
    
    if not case.patient:
        logging.error("No patient found found inside %s, will not be downloaded to phone" % case)
        return
    
    open_inner_cases = [cinner for cinner in case.commcare_cases if not cinner.closed]
    if len(open_inner_cases) == 0:
        logging.error("No open case found inside %s, will not be downloaded to phone" % case)
        return
    elif len(open_inner_cases > 1):
        logging.error("More than one open case found inside %s.  Only the most recent will not be downloaded to phone" % case)
        ccase = sorted(open_inner_cases, key=lambda case: case.opened_on)[0]
    else:
        ccase = open_inner_cases[0]
    
    
    # this currently dumps everything in a single update block
    # TODO: this doesn't feel like a final way to do this
    return CASE_TEMPLATE % {"case_id": ccase._id,
                            "date_modified":case.modified_on,
                            "case_type_id": const.CASE_TYPE_BHOMA_FOLLOWUP,
                            "user_id": ccase.user_id,
                            "case_name": case.case_name,
                            "external_id": case.external_id,
                            "first_name": case.first_name,
                            "last_name": case.last_name,
                            "birth_date": case.birth_date,
                            "birth_date_est": case.birth_date_est,
                            "age": case.age,
                            "sex": case.sex,
                            "village": case.village,
                            "contact": case.contact,
                            "bhoma_case_id": case.bhoma_case_id,
                            "bhoma_patient_id": case.bhoma_patient_id,
                            
                            "followup_type": case.followup_type,
                            "orig_visit_type": case.orig_visit_type,
                            "orig_visit_diagnosis": case.orig_visit_diagnosis,
                            "orig_visit_date": case.orig_visit_date,
                            "activation_date": case.activation_date,
                            "due_date": case.due_date,
                            
                            "missed_appt_date": case.missed_appt_date,
                            "ttl_missed_apts": case.ttl_missed_apts,
                            
                            "current_followup_status": case.current_followup_status}
