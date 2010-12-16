from django.test import TestCase
from django.conf import settings
from couchdbkit import *
from bhoma.utils.data import random_clinic_id, random_person
import os
from bhoma.apps.xforms.util import post_xform_to_couch
from bhoma.apps.patient.processing import add_form_to_patient, new_form_received,\
    new_form_workflow
from bhoma.apps.reports.models import CPregnancy
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.xforms.models.couch import CXFormInstance


class PregnancyTest(TestCase):
    
    def setUp(self):
        for item in CXFormInstance.view("xforms/xform").all():
            item.delete()       
        
    def testNVP(self):

        # Not testing positive
        p = random_person()
        p.save()
        post_and_process_xform("preg_no_hiv_test_1.xml", p)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p.get_id).one()
        self.assertEqual(False, pregnancy.got_nvp_when_tested_positive)
        
        # Test positive subsequent visit
        post_and_process_xform("preg_hiv_pos_2.xml", p)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p.get_id).one()
        self.assertEqual(True, pregnancy.got_nvp_when_tested_positive)
        
        p2 = random_person()
        p2.save()
        # Testing positive but already on Haart
        post_and_process_xform("preg_hiv_pos_1.xml", p2)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p2.get_id).one()
        self.assertEqual(False, pregnancy.got_nvp_when_tested_positive)
        
        
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
    
        