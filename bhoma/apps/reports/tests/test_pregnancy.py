from django.test import TestCase
from django.conf import settings
from couchdbkit import *
from bhoma.utils.data import random_clinic_id, random_person
import os
from bhoma.apps.xforms.util import post_xform_to_couch
from bhoma.apps.patient.processing import add_new_clinic_form
from bhoma.apps.reports.models import CPregnancy


class PregnancyTest(TestCase):
    
    def setUp(self):
        pass
    
    def testHIVTestDone(self):
        # no hiv on first visit
        p = random_person()
        p.save()
        post_and_process_xform("preg_no_hiv_1.xml", p)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p.get_id).one()
        self.assertEqual(False, pregnancy.hiv_test_done)
        
        # but add it on a subsequent visit
        post_and_process_xform("preg_no_hiv_2.xml", p)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p.get_id).one()
        self.assertEqual(True, pregnancy.hiv_test_done)
        
        p2 = random_person()
        p2.save()
        post_and_process_xform("start_preg_hiv.xml", p2)
        pregnancy = CPregnancy.view("reports/pregnancies_for_patient", key=p2.get_id).one()
        self.assertEqual(True, pregnancy.hiv_test_done)
        
        
        
def post_and_process_xform(filename, patient):
    doc = post_xform(filename, patient.get_id)    
    add_new_clinic_form(patient, doc)
    return doc
    
        
def post_xform(filename, patient_id):    
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    xml_data = open(file_path, "rb").read()
    xml_data = xml_data.replace("REPLACE_PATID", patient_id)
    doc = post_xform_to_couch(xml_data)
    return doc
    
        