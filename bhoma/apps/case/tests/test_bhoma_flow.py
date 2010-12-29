from datetime import date
from django.test import TestCase
from bhoma.apps.case.tests.util import bhoma_case_from_xml
import uuid

class CaseFromBhomaXFormTest(TestCase):
    
    def testClosed(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_closed.xml", 
                                   pat_id_override=pat_id)
        self.assertEqual(pat_id, case["patient_id"])
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(True, case.closed)
        self.assertEqual("sick", case.type)
        self.assertEqual("all better", case.outcome)
        self.assertEqual(date(2010,06,01), case.opened_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(2, len(cccase.actions))
        self.assertEqual(0, len(cccase.referrals))
        
        
    
    def testChwFollow(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_chw_follow.xml",
                                   pat_id_override=pat_id)
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(1, len(cccase.actions))
        self.assertEqual(0, len(cccase.referrals))
        self.assertEqual(date(2010,6,1), case.opened_on.date())
        self.assertEqual("chw", cccase.followup_type)
        self.assertEqual(date(2010,6,13), cccase.due_date)
        