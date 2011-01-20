from django.test import TestCase
from bhoma.apps.patient import export as export
import os
from bhoma.apps.case.const import Outcome

class DeathTest(TestCase):
    
    def testDeathAfter(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "death_after")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        self.assertFalse(patient.is_deceased)
        # enter a form with outcome death
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        # enter a form with a different outcome that should create a case
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        # make sure the second case is closed and the outcome is also death 
        self.assertTrue(updated_patient.is_deceased)
        self.assertEqual(2, len(updated_patient.cases))
        for case in updated_patient.cases:
            self.assertTrue(case.closed)
            self.assertEqual(Outcome.PATIENT_DIED, case.outcome)
            
    def testDeath(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "death_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        self.assertFalse(patient.is_deceased)
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        self.assertTrue(updated_patient.is_deceased)
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(updated_patient.is_deceased)
        self.assertEqual("cardiac_failure", case.type)
        self.assertEqual(Outcome.PATIENT_DIED, case.outcome)
        self.assertEqual(0, len(case.commcare_cases))
    
    