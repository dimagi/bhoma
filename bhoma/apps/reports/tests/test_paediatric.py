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


class PaediatricTest(TestCase):
    
    def setUp(self):
        for item in CXFormInstance.view("xforms/xform").all():
            item.delete()
    
    def testHIVTestDone(self):
        #case1: already exposed, don't need to order test (0,0)
        p = random_person()
        p.save()
        post_and_process_xform("paed_hiv_1_no_test.xml", p)
        self.assertEqual(False, ...)
        
        #case2: no card, has symptoms, not tested (0,1)
        post_and_process_xform("paed_hiv_2_test_nd.xml", p)
        
        #case3: hiv result nr, has symptoms, tested (1,1)
        post_and_process_xform("paed_hiv_3_tested.xml", p)

        #case4: hiv status unknown, no prev test result, tested (1,1)
        post_and_process_xform("paed_hiv_4_tested.xml", p)        
        
        
    def testFever(self):
        
        p = random_person()
        p.save()

        #case1: high temp, rdt neg, antimalarial (0,1)
        post_and_process_xform("paed_fever_1.xml", p)
        
        #case2: fever assess, blank fever symp, danger sign, rdt neg, antibiotic (1,1)
        post_and_process_xform("paed_fever_2_neg.xml", p)

        #case3: fever assess, rdt pos, antibiotic (0,1)
        post_and_process_xform("paed_fever_3_pos.xml", p)

        #case4: fever assess, rdt pos, antimalarial (1,1)
        post_and_process_xform("paed_fever_4_pos.xml", p)

        #case5: fever assess, rdt neg, no drugs (1,1)
        post_and_process_xform("paed_fever_5_neg.xml", p)

    def testDiarrhea(self):
        
        p = random_person()
        p.save()

        #case1: diarrhea assess, danger sign, fluids (1,1)
        post_and_process_xform("paed_diarrhea_1.xml", p)
        
        #case2: diarrhea assess, mod sympt, ors (1,1)
        post_and_process_xform("paed_diarrhea_2.xml", p)
        
        #case3: diarrhea assess, sev sympt, ors (0,1)
        post_and_process_xform("paed_diarrhea_3.xml", p)
        
        #case4: diarrhea assess, sev sympt, ringers (1,1)
        post_and_process_xform("paed_diarrhea_4.xml", p)
               
        #case5: diarrhea assess, sev sympt, bloody stool, antibiotic, ringers (1,1)
        post_and_process_xform("paed_diarrhea_5.xml", p)             
              
        #case6: diarrhea assess, sev sympt, bloody stool, no antibiotic, ringers (0,1)
        post_and_process_xform("paed_diarrhea_6.xml", p)    
              
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
    
        