from datetime import date
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
        self.assertEqual(date(2010,06,01), case.opened_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(2, len(cccase.actions))
        self.assertEqual(0, len(cccase.referrals))
        
        
    
    def testChwFollow(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_chw_follow.xml", "general_visit",
                                   pat_id_override=pat_id)
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(1, len(cccase.actions))
        self.assertEqual(1, len(cccase.referrals))
        self.assertEqual(date(2010,6,1), case.opened_on.date())
        ref = cccase.referrals[0]
        self.assertEqual("general_visit|sick|followup-chw", ref.type)
        self.assertEqual(date(2010,6,8), ref.followup_on.date())
        
    def testClinicFollow(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_clinic_follow.xml", "general_visit",
                                   pat_id_override=pat_id)
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(1, len(cccase.actions))
        self.assertEqual(1, len(cccase.referrals))
        self.assertEqual(date(2010,6,1), case.opened_on.date())
        ref = cccase.referrals[0]
        self.assertEqual("general_visit|sick|followup-chw", ref.type)
        self.assertEqual(date(2010,6,8), ref.followup_on.date())
    
    def testRefer(self):
        pat_id = uuid.uuid4().hex 
        case = bhoma_case_from_xml(self, "bhoma/bhoma_create_refer.xml", "general_visit",
                                   pat_id_override=pat_id)
        self.assertNotEqual(pat_id, case._id)
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.commcare_cases))
        cccase = case.commcare_cases[0]
        self.assertEqual(1, len(cccase.actions))
        self.assertEqual(1, len(cccase.referrals))
        self.assertEqual(date(2010,6,1), case.opened_on.date())
        ref = cccase.referrals[0]
        self.assertEqual("general_visit|sick|followup-chw", ref.type)
        self.assertEqual(date(2010,6,8), ref.followup_on.date())
        
        
