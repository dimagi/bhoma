from django.test import TestCase
from bhoma.apps.patient import export as export
import os

class ImportExportTestCase(TestCase):
    
    def testImportFromZip(self):
        file_name = os.path.join(os.path.dirname(__file__), "testdata", "export_test.zip")
        patient = export.import_patient_zip(file_name)
        self.assertEqual("EXPORT", patient.first_name)
        self.assertEqual("TEST", patient.last_name)
        self.assertEqual("f", patient.gender)
        self.assertEqual(3, len(patient.encounters))
        
        
    def testImportFromFolder(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testdata", "export_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        # forms are loaded one at a time.  If you need to run tests at 
        # intermediate states, put them in between whatever forms you
        # want loaded
        self.assertEqual("EXPORT", patient.first_name)
        self.assertEqual("TEST", patient.last_name)
        self.assertEqual("f", patient.gender)
        self.assertEqual(0, len(patient.encounters))
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_sick_pregnancy.xml"))
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_general.xml"))
        
        # custom test conditions after all forms are loaded go here 
        self.assertEqual(3, len(updated_patient.encounters))
        