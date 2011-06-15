from django.test import TestCase
from bhoma.apps.patient import export as export
import os
from couchlog.models import ExceptionRecord

class TestBugs(TestCase):
    
    def setUp(self):
        for item in ExceptionRecord.view("couchlog/all_by_date", include_docs=True).all():
            item.delete()
    
    def testPostSaveDrugBug(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date", include_docs=True).all()))
        folder_name = os.path.join(os.path.dirname(__file__), "testdata", "test_post_save_drug_bug")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_underfive.xml"))
        
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date", include_docs=True).all()))
        