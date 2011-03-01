from django.test import TestCase
import os
from datetime import datetime
from bhoma.apps.patient import export
from bhoma.apps.case.bhomacaselogic.shared import jr_float_to_string_int
from bhoma.apps.xforms.util import post_xform_to_couch
from bhoma.apps.patient.processing import new_form_workflow, reprocess
from bhoma.apps.patient.signals import SENDER_PHONE
from bhoma.apps.patient.models import CPatient
from bhoma.apps.case.bhomacaselogic.shared import get_latest_patient_id_format
from django.test.client import Client
from django.core.urlresolvers import reverse
from bhoma.apps.case.tests.util import check_xml_line_by_line
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma import const
from bhoma.utils.cleanup import delete_all_xforms, delete_all_patients

class IdFormatTest(TestCase):
    
    def testJavaRosaIds(self):
        ID = "5040120123450"
        for f in ["5040120123450", "5.04012012345E12", "5.040120123450E12",
                  "50.40120123450e11", 5040120123450, 5040120123450.0]:
            self.assertEqual(ID, jr_float_to_string_int(f), "%s doesn't match" % f)
            
    def testIdUpgrade(self):
        ID = "5040120123450"
        for f in ["5040120123450", "504120123450"]:
            self.assertEqual(ID, get_latest_patient_id_format(f), "%s doesn't match" % f)
        
    
class ReferralTest(TestCase):
    """
    Test for the referral/follow up logic.
    
    Currently life-threatening referrals are meant to generate a bhoma case
    that goes to the CHW if the patient doesn't show up within one week.
    """

    def setUp(self):
        # delete our patients and forms before each test
        delete_all_patients()
        delete_all_xforms()
    
    def testNonLifeThreatening(self):
        folder_name = os.path.join(os.path.dirname(__file__), "data", "chw")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        self.assertEqual(0, len(patient.encounters))
        self.assertEqual(0, len(patient.cases))
        with open(os.path.join(folder_name, "non_life_threatening_referral.xml"), "r") as f:
            formbody = f.read()
        formdoc = post_xform_to_couch(formbody)
        new_form_workflow(formdoc, SENDER_PHONE, None)
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.encounters))
        [case] = patient.cases
        self.assertEqual(0, len(case.commcare_cases))
        
    def testRegeneratePatient(self):
        folder_name = os.path.join(os.path.dirname(__file__), "data", "chw")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        self.assertEqual(0, len(patient.encounters))
        with open(os.path.join(folder_name, "non_life_threatening_referral.xml"), "r") as f:
            formbody = f.read()
        formdoc = post_xform_to_couch(formbody)
        new_form_workflow(formdoc, SENDER_PHONE, None)
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.encounters))
        self.assertTrue(reprocess(patient.get_id))
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.encounters))
        
    def testLifeThreatening(self):
        folder_name = os.path.join(os.path.dirname(__file__), "data", "chw")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        self.assertEqual(0, len(patient.encounters))
        self.assertEqual(0, len(patient.cases))
        with open(os.path.join(folder_name, "life_threatening_referral.xml"), "r") as f:
            formbody = f.read()
        formdoc = post_xform_to_couch(formbody)
        new_form_workflow(formdoc, SENDER_PHONE, None)
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.encounters))
        [case] = patient.cases
        [ccase] = case.commcare_cases
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[patient.get_id]))
        expected_xml = """<cases>
<case>
    <case_id>02UDZM6C6MGISTFW5REZ35D3N-a8399bfabc1f827e180522bc7a9cecf13d7290f1-a8399bfabc1f827e180522bc7a9cecf13d7290f1</case_id> 
    <date_modified>%(today)s</date_modified>
    <create>
        <case_type_id>bhoma_followup</case_type_id> 
        <user_id>404a6c3e54bfcc2793daa43baafbe410</user_id> 
        <case_name>new_clinic_referral|fever headache</case_name> 
        <external_id>02UDZM6C6MGISTFW5REZ35D3N-a8399bfabc1f827e180522bc7a9cecf13d7290f1</external_id>
    </create>
    <update>
        <first_name>REF</first_name>
        <last_name>TEST</last_name>
        <birth_date>1982-06-17</birth_date>
        <birth_date_est>False</birth_date_est>
        <age>28</age>
        <sex>f</sex>
        <village>O</village>
        <contact>5</contact>
        <bhoma_case_id>02UDZM6C6MGISTFW5REZ35D3N-a8399bfabc1f827e180522bc7a9cecf13d7290f1</bhoma_case_id>
        <bhoma_patient_id>ab3d4dc25a4d3261f4b5c5042c5279ac7</bhoma_patient_id>
        <followup_type>referral_no_show</followup_type>
        <orig_visit_type>new_clinic_referral</orig_visit_type>
        <orig_visit_diagnosis>fever headache</orig_visit_diagnosis>
        <orig_visit_date>2011-02-03</orig_visit_date>
        <activation_date>2011-02-06</activation_date>
        <due_date>2011-02-06</due_date>
        <missed_appt_date>2011-02-04</missed_appt_date>
    </update>
</case>
</cases>""" % {"today": date_to_xml_string(datetime.utcnow().date())}
        check_xml_line_by_line(self, expected_xml, response.content)
        
    def testUnmatchedPatient(self):
        folder_name = os.path.join(os.path.dirname(__file__), "data", "chw")
        with open(os.path.join(folder_name, "non_life_threatening_referral.xml"), "r") as f:
            formbody = f.read()
        formdoc = post_xform_to_couch(formbody)
        new_form_workflow(formdoc, SENDER_PHONE, None)
        self.assertFalse("#patient_guid" in formdoc)
        
    def testMissingPatientId(self):
        folder_name = os.path.join(os.path.dirname(__file__), "data", "chw")
        with open(os.path.join(folder_name, "referral_no_pat_id.xml"), "r") as f:
            formbody = f.read()
        formdoc = post_xform_to_couch(formbody)
        new_form_workflow(formdoc, SENDER_PHONE, None)
        self.assertFalse("#patient_guid" in formdoc)
