from django.test import TestCase
from bhoma.apps.case.tests.util import bhoma_case_from_xml
import uuid

class CaseFromBhomaXFormTest(TestCase):
    
    def testClosed(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_closed.xml", "general_visit", 
                                   pat_id_override=pat_id)
        self.assertEqual(pat_id, case["patient_id"])
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(True, case.closed)
        self.assertEqual("sick", case.type)
        self.assertEqual("all better", case.outcome)
        self.assertEqual(2, len(case.actions))
        
    
    def testChwFollowType(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_chw_follow.xml", "general_visit",
                                   pat_id_override=pat_id)
        