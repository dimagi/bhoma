import os
import uuid
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.case.xform import get_or_update_cases
from bhoma.utils.post import post_data
from django.conf import settings

def bootstrap_case_from_xml(test_class, filename, case_id_override=None,
                                 referral_id_override=None):
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    xml_data = open(file_path, "rb").read()
    doc_id, uid, case_id, ref_id = replace_ids_and_post(xml_data, case_id_override=case_id_override, 
                                                         referral_id_override=referral_id_override)  
    cases_touched = get_or_update_cases(CXFormInstance.get_db().get(doc_id))
    test_class.assertEqual(1, len(cases_touched))
    case = cases_touched[case_id]
    test_class.assertEqual(case_id, case.case_id)
    return case
            

        
def replace_ids_and_post(xml_data, case_id_override=None, referral_id_override=None):
    # from our test forms, replace the UIDs so we don't get id conflicts
    uid, case_id, ref_id = (uuid.uuid4().hex for i in range(3))
    
    if case_id_override:      case_id = case_id_override
    if referral_id_override:  ref_id = referral_id_override
        
    xml_data = xml_data.replace("REPLACE_UID", uid)
    xml_data = xml_data.replace("REPLACE_CASEID", case_id)
    xml_data = xml_data.replace("REPLACE_REFID", ref_id)
    doc_id, _ = post_data(xml_data, settings.XFORMS_POST_URL )
    return (doc_id, uid, case_id, ref_id)
    
    