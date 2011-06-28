from django.test import TestCase
import os
from bhoma.utils.cleanup import delete_all_xforms
from bhoma.apps.patient import export
from bhoma.apps.reports import const
from dimagi.utils.couch.database import get_db


class PaediatricTest(TestCase):
    
    def setUp(self):
        delete_all_xforms()
        
    def testHIVTestDone(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "paed_hiv")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # first visit has a recent test so it doesn't count to denominator
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_underfive.xml"))
        [res] = get_db().view(const.get_view_name("under_5_pi"), group=True, group_level=4, 
                            key=[2011,4, "9999999", "hiv_test"]).all()
        num, denom = res["value"]
        self.assertEqual(0, num)
        self.assertEqual(0, denom)
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_underfive.xml"))
        
        # second visit has no recent test so it counts
        [res] = get_db().view(const.get_view_name("under_5_pi"), group=True, group_level=4, 
                            key=[2011,5, "9999999", "hiv_test"]).all()
        num, denom = res["value"]
        self.assertEqual(0, num)
        self.assertEqual(1, denom)
            
        