from django.test import TestCase
from datetime import date, datetime
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line

class PregnancyObjectTest(TestCase):

    def testFirstVisitSick(self):
        # initial visit sick
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "pregnancy_sickvisit")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_sick_pregnancy.xml"))
        self.assertEqual(1, len(updated_patient.pregnancies))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,1,5), preg.edd)
        self.assertEqual(form_doc1.get_id, preg.anchor_form_id)
        self.assertEqual(0, len(preg.other_form_ids))
        
        # add a healthy visit after, should be part of the same pregnancy
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,1,5), preg.edd)
        self.assertEqual(form_doc1.get_id, preg.anchor_form_id)
        self.assertEqual(1, len(preg.other_form_ids))
        self.assertEqual(form_doc2.get_id, preg.other_form_ids[0])
        
        # add a healthy visit before, should be part of the same pregnancy, 
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,1,5), preg.edd)
        # should not change anchor
        self.assertEqual(form_doc1.get_id, preg.anchor_form_id)
        self.assertEqual(2, len(preg.other_form_ids))
        
    def testHealthyPregnancyLMP(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,3,8), preg.edd)
        
        
    
    def testHealthyPregnancyEDD(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,2,10), preg.edd)
        
    
    def testHealthyPregnancyGestationalAge(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,1,14), preg.edd)
        
    def testHealthyPregnancyMisingEDD(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc4 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "004_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(None, preg.edd)
        
    def testSickPregnancyGestationalAge(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc5 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "005_sick_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(date(2011,3,21), preg.edd)
        
    def testSickPregnancyMissingEDD(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "edd_conditions")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc6 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "006_sick_pregnancy.xml"))
        [preg] = updated_patient.pregnancies
        self.assertEqual(None, preg.edd)
                