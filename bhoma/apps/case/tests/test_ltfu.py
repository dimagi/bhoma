from django.test import TestCase
from bhoma.apps.patient import export as export
import os
from bhoma.apps.patient.processing import reprocess
from bhoma.apps.case import const
from bhoma.apps.patient.models.couch import CPatient

class LtfuCaseTest(TestCase):
    
    def testLostImmediatelyCloses(self):
        """
        Creates a case that is too long ago and is lost and therefore is 
        closed as such.
        """
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "ltfu_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.outcome.startswith("lost_to_followup"))
        self.assertEqual(case.closed_on.date(), case.ltfu_date)
        [ccase] = case.commcare_cases
        self.assertTrue(ccase.closed)
        
    
    def testReturnToClinicSupercedes(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "ltfu_test2")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_general.xml"))
        
        reprocess(updated_patient.get_id)
        updated_patient = CPatient.get(updated_patient.get_id)
        self.assertEqual(3, len(updated_patient.cases))
        [c1, c2, c3] = sorted(updated_patient.cases, key=lambda case: case.opened_on)
        
        # after reprocessing the first case should be closed with returned to clinic, 
        # but the second should be ltfu
        self.assertTrue(c1.closed)
        self.assertEqual(const.Outcome.RETURNED_TO_CLINIC, c1.outcome)
        self.assertTrue(c2.closed)
        self.assertEqual(const.Outcome.LOST_TO_FOLLOW_UP, c2.outcome)
        
    def testOutOfOrderLoss(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "ltfu_test2")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # make sure we properly handle when the forms come out of order
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_general.xml"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        [c2, c3] = sorted(updated_patient.cases, key=lambda case: case.opened_on)
        self.assertTrue(c2.closed)
        self.assertEqual(const.Outcome.LOST_TO_FOLLOW_UP, c2.outcome)
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        [c1, c2, c3] = sorted(updated_patient.cases, key=lambda case: case.opened_on)
        self.assertTrue(c1.closed)
        self.assertEqual(const.Outcome.RETURNED_TO_CLINIC, c1.outcome)
        
    
        
    
        