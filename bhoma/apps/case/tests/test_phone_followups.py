from datetime import datetime, date, timedelta
from django.test import TestCase
from bhoma.apps.patient import export as export
import os
from bhoma.apps.xforms.util import post_xform_to_couch
from bhoma.apps.patient.processing import new_form_workflow

folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "phone_followups")

class PhoneFollowupTest(TestCase):
    
    def setUp(self):
        self.patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
    def tearDown(self):
        self.patient.delete()
        
    def _check_initial_config(self, updated_patient, form_doc):
        # check encounter
        self.assertEqual(1, len(updated_patient.encounters))
        [encounter] = updated_patient.encounters
        self.assertEqual(encounter.get_xform().sha1, form_doc.sha1)
        
        # check case
        self.assertEqual(1, len(updated_patient.cases))
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual(None, case.outcome)
        self.assertTrue(case.send_to_phone)
        self.assertEqual(encounter.visit_date, case.opened_on.date())
        self.assertEqual(datetime.utcnow().date(), case.modified_on.date())
        
        # check commcare case
        [ccase] = case.commcare_cases
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        days = int(form_doc.xpath("case/followup_date"))
        self.assertEqual(case.opened_on.date() + timedelta(days=days + 3), ccase.activation_date)
        self.assertEqual(case.opened_on.date() + timedelta(days=days + 13), ccase.due_date)
        self.assertEqual(case.opened_on.date() + timedelta(days=days + 3), ccase.start_date)
    
    def testFollowNoPatient(self):
        # no assertions necessary, this should just not throw an exception
        with open(os.path.join(os.path.dirname(__file__), "data", "bhoma", "chw_followup_nopatient.xml"), "r") as f:
            formdoc = post_xform_to_couch(f.read())
            new_form_workflow(formdoc, None, None)
            
        
        
    def testMetFeelingBetter(self):
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "001_general.xml"))
        self._check_initial_config(updated_patient, form_doc1)
        
        # follow up
        updated_patient, form_doc = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "008_chw_fu.xml"))
        
        # check encounter
        self.assertEqual(2, len(updated_patient.encounters))
        encounter = updated_patient.encounters[1]
        self.assertEqual(encounter.get_xform().sha1, form_doc.sha1)
        
        # check case
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertEqual(encounter.visit_date, case.closed_on.date())
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("primary_diagnosis_resolved", case.outcome)
        
        # check commcare case
        [ccase] = case.commcare_cases
        self.assertTrue(ccase.closed)
        # TODO: fix this
        self.assertEqual(encounter.visit_date, ccase.closed_on.date())
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        
        
    def testMetStillSickReturnYes(self):
        updated_patient, form_doc4 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "004_general.xml"))
        self._check_initial_config(updated_patient, form_doc4)
        
        updated_patient, form_doc11 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "011_chw_fu.xml"))
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual(None, case.outcome)
        
    def testMetStillSickReturnNo(self):
        
        updated_patient, form_doc5 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "005_general.xml"))
        self._check_initial_config(updated_patient, form_doc5)
        
        updated_patient, form_doc12 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "012_chw_fu.xml"))
        
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual(None, case.outcome)
        
        updated_patient, form_doc15 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "015_chw_fu.xml"))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("primary_diagnosis_resolved", case.outcome)
        
    def testMetNewComplaintReturnYes(self):
        
        updated_patient, form_doc6 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "006_general.xml"))
        self._check_initial_config(updated_patient, form_doc6)
        
        updated_patient, form_doc13 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "013_chw_fu.xml"))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("primary_diagnosis_resolved", case.outcome)
        
        
    def testMetNewComplaintReturnNo(self):
        
        updated_patient, form_doc7 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "007_general.xml"))
        self._check_initial_config(updated_patient, form_doc7)
        
        updated_patient, form_doc14 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "014_chw_fu.xml"))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("primary_diagnosis_resolved", case.outcome)
        
        
    def testNoMetThenMet(self):
        updated_patient, form_doc3 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "003_general.xml"))
        self._check_initial_config(updated_patient, form_doc3)
        
        updated_patient, form_doc9 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "009_chw_fu.xml"))
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("pending chw meeting", case.status)
        self.assertEqual(None, case.outcome)
        
        updated_patient, form_doc10 = export.add_form_file_to_patient(self.patient.get_id, os.path.join(folder_name, "010_chw_fu.xml"))
        
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("pending chw meeting", case.status)
        self.assertEqual("primary_diagnosis_resolved", case.outcome)
        
    