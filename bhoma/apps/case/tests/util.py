import os
import uuid
from datetime import datetime, timedelta
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.case.xform import get_or_update_cases
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.encounter.models import Encounter
from dimagi.utils.dates import safe_date_add
from bhoma.apps.xforms.util import post_from_settings
from bhoma.apps.patient import export

def replace_date(contents, days_from_today=0, date_template_tag="date", 
                 format_string="%Y-%m-%d"):
    """
    Take in a string, replace all instances of the date_template_tag 
    in the string with a new date, offset from today or by default
    using today's date.
    """
    date_to_use = datetime.utcnow().date() + timedelta(days=days_from_today)
    return contents % {date_template_tag: date_to_use.strftime(format_string)}
    
def add_form_with_date_offset(patient_id, filename, days_from_today=0, 
                              date_template_tag="date", format_string="%Y-%m-%d"):
    """
    Like the export command to add forms to patients, but allows you to 
    pass in date offsets for specific tags in the XML so that you can 
    control the dates getting set in the test
    """
    with open(filename) as f:
        form_with_updated_date = replace_date(f.read(), days_from_today=days_from_today,
                                              date_template_tag=date_template_tag, 
                                              format_string=format_string)
        return export.add_form_to_patient(patient_id, form_with_updated_date)
        
def bootstrap_case_from_xml(test_class, filename, case_id_override=None,
                                 referral_id_override=None):
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(file_path, "rb") as f:
        xml_data = f.read()
    doc_id, uid, case_id, ref_id = replace_ids_and_post(xml_data, case_id_override=case_id_override, 
                                                         referral_id_override=referral_id_override)  
    cases_touched = get_or_update_cases(CXFormInstance.get(doc_id))
    test_class.assertEqual(1, len(cases_touched))
    case = cases_touched[case_id]
    test_class.assertEqual(case_id, case.case_id)
    return case
            
def bhoma_case_from_xml(test_class, filename, pat_id_override=None,
                        referral_id_override=None):
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(file_path, "rb") as f:
        xml_data = f.read()
    doc_id, uid, case_id, ref_id = replace_ids_and_post(xml_data, case_id_override=pat_id_override, 
                                                         referral_id_override=referral_id_override)
    doc = CXFormInstance.get(doc_id)
    encounter = Encounter.from_xform(doc)  
    case = get_or_update_bhoma_case(doc, encounter)
    test_class.assertNotEqual(None, case)
    return case
        
def replace_ids_and_post(xml_data, case_id_override=None, referral_id_override=None):
    # from our test forms, replace the UIDs so we don't get id conflicts
    uid, case_id, ref_id = (uuid.uuid4().hex for i in range(3))
    
    if case_id_override:      case_id = case_id_override
    if referral_id_override:  ref_id = referral_id_override
        
    xml_data = xml_data.replace("REPLACE_UID", uid)
    xml_data = xml_data.replace("REPLACE_CASEID", case_id)
    xml_data = xml_data.replace("REPLACE_REFID", ref_id)
    doc_id, errors = post_from_settings(xml_data)
    if errors: 
        raise Exception("Couldn't post! %s" % errors)
    elif "error" in doc_id:
        raise Exception("Problem with couch! %s" % doc_id)
    return (doc_id, uid, case_id, ref_id)
    
def check_xml_line_by_line(test_case, expected, actual, ignore_whitespace=True, delimiter="\n"):
    """Does what it's called, hopefully parameters are self-explanatory"""
    if ignore_whitespace:
        expected = expected.strip()
        actual = actual.strip()
    expected_lines = expected.split("\n")
    actual_lines = actual.split(delimiter)
    test_case.assertEqual(len(expected_lines), len(actual_lines)) 
    for i in range(len(expected_lines)):
        if ignore_whitespace:
            test_case.assertEqual(expected_lines[i].strip(), actual_lines[i].strip())
        else:
            test_case.assertEqual(expected_lines[i], actual_lines[i])
        
    
def check_commcare_dates(test_case, case, ccase,  
                         start_days, active_days, due_days, ltfu_days=42):
    
    test_case.assertEqual(ccase.start_date, safe_date_add(case.opened_on, start_days))
    test_case.assertEqual(ccase.activation_date, safe_date_add(case.opened_on, active_days))
    test_case.assertEqual(ccase.due_date, safe_date_add(case.opened_on, due_days))
    test_case.assertEqual(case.ltfu_date, safe_date_add(case.opened_on, ltfu_days))
