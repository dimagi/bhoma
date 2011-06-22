from django.test import TestCase
from couchdbkit import *
from bhoma.utils.data import random_person
import os
from bhoma.apps.xforms.util import post_xform_to_couch

from bhoma.apps.patient.processing import new_form_workflow
from bhoma.apps.reports.models import PregnancyReportRecord

from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.utils.cleanup import delete_all_xforms
from bhoma.apps.patient import export



class PregnancyTest(TestCase):
    
    def setUp(self):
        delete_all_xforms()
        
    def testNVP(self):

        # Not testing positive
        p = random_person()
        p.save()
        post_and_process_xform("preg_no_hiv_test_1.xml", p)
        pregnancy = PregnancyReportRecord.view("reports/pregnancies_for_patient", key=p.get_id, include_docs=True).one()
        self.assertEqual(False, pregnancy.got_nvp_when_tested_positive)
        
        # Test positive subsequent visit
        post_and_process_xform("preg_hiv_pos_2.xml", p)
        pregnancy = PregnancyReportRecord.view("reports/pregnancies_for_patient", key=p.get_id, include_docs=True).one()
        self.assertEqual(True, pregnancy.got_nvp_when_tested_positive)
        
        p2 = random_person()
        p2.save()
        # Testing positive but already on Haart
        post_and_process_xform("preg_hiv_pos_1.xml", p2)
        pregnancy = PregnancyReportRecord.view("reports/pregnancies_for_patient", key=p2.get_id, include_docs=True).one()
        self.assertEqual(False, pregnancy.got_nvp_when_tested_positive)
    
    def testFansidar(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "fansidar")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        def _latest_pregnancy():
            return PregnancyReportRecord.view("reports/pregnancies_for_patient", 
                                               key=updated_patient.get_id, 
                                               include_docs=True).one()
        # dose 1
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"))
        pregnancy = _latest_pregnancy()
        self.assertFalse(pregnancy.eligible_three_doses_fansidar)
        self.assertFalse(pregnancy.got_three_doses_fansidar)
        
        # dose 2
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_pregnancy.xml"))
        pregnancy = _latest_pregnancy()
        self.assertFalse(pregnancy.eligible_three_doses_fansidar)
        self.assertFalse(pregnancy.got_three_doses_fansidar)
        
        # sick visit, doesn't count
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_sick_pregnancy.xml"))
        pregnancy = _latest_pregnancy()
        self.assertFalse(pregnancy.eligible_three_doses_fansidar)
        self.assertFalse(pregnancy.got_three_doses_fansidar)
        
        # healthy visit, no fansidar count
        updated_patient, form_doc4 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "004_pregnancy.xml"))
        pregnancy = _latest_pregnancy()
        self.assertTrue(pregnancy.eligible_three_doses_fansidar)
        self.assertFalse(pregnancy.got_three_doses_fansidar)
        
        # healthy visit fansidar 
        updated_patient, form_doc5 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "005_pregnancy.xml"))
        pregnancy = _latest_pregnancy()
        self.assertTrue(pregnancy.eligible_three_doses_fansidar)
        self.assertTrue(pregnancy.got_three_doses_fansidar)
                
def post_and_process_xform(filename, patient):
    doc = post_xform(filename, patient.get_id)
    new_form_workflow(doc, "unit_tests", patient.get_id)
    return doc
    
        
def post_xform(filename, patient_id):    
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(file_path, "rb") as f:
        xml_data = f.read()
    xml_data = xml_data.replace("REPLACE_PATID", patient_id)
    doc = post_xform_to_couch(xml_data)
    return doc
    
        
