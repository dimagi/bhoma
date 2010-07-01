import os
import uuid
import tempfile
from datetime import datetime
from django.test import TestCase
from django.conf import settings
from bhoma.apps.xforms.models import XForm
from bhoma.apps.case.models import CCase
from bhoma.utils.post import post_file, post_data
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.case.xform import get_or_update_cases
from bhoma.apps.case import const

# these match properties in the xml
ORIGINAL_DATE = datetime(2010, 06, 29, 13, 42, 50)
MODIFY_DATE = datetime(2010, 06, 30, 13, 42, 50)
UPDATE_DATE = datetime(2010, 05, 12, 13, 42, 50)
CLOSE_DATE = datetime(2010, 07, 1, 13, 42, 50)
REFER_DATE = datetime(2010, 07, 2, 13, 42, 50)

class CaseFromXFormTest(TestCase):
    
    def testCreate(self):
        case = self._bootstrap_case_from_xml("create.xml")
        self._check_static_properties(case)
        self.assertEqual(False, case.closed)
        
        self.assertEqual(1, len(case.actions))
        create_action = case.actions[0]
        self.assertEqual(const.CASE_ACTION_CREATE, create_action.action_type)
        
        self.assertEqual(0, len(case.referrals))
    
    def testCreateAndUpdateInSingleBlock(self):
        case = self._bootstrap_case_from_xml("create_update.xml")
        self._check_static_properties(case)
        self.assertEqual(False, case.closed)
        self.assertEqual(2, len(case.actions))
        create_action = case.actions[0]
        update_action = case.actions[1]
        self.assertEqual(const.CASE_ACTION_CREATE, create_action.action_type)
        self.assertEqual(const.CASE_ACTION_UPDATE, update_action.action_type)
        
        # make sure the update properties are in both the update action
        # and the case itself.
        self.assertEqual("abc", case["someprop"])
        self.assertEqual("abc", update_action["someprop"])
        
        # there's some string/integer wackiness i'm not going to address here
        # going on, just compare everything as strings
        self.assertEqual("123", str(case["someotherprop"]))
        self.assertEqual("123", str(update_action["someotherprop"]))
        
        self.assertEqual(0, len(case.referrals))

    def testCreateThenUpdateInSeparateForms(self):
        # recycle our previous test's form
        original_case = self._bootstrap_case_from_xml("create_update.xml")
        original_case.save()
        
        # we don't need to bother checking all the properties because this is
        # the exact same workflow as above.
        case = self._bootstrap_case_from_xml("update.xml", original_case.case_id)
        self.assertEqual(False, case.closed)
        
        self.assertEqual(3, len(case.actions))
        new_update_action = case.actions[2]
        self.assertEqual(const.CASE_ACTION_UPDATE, new_update_action.action_type)
        
        # some properties didn't change
        self.assertEqual("123", str(case["someotherprop"]))
        
        # but some should have
        self.assertEqual("abcd", case["someprop"])
        self.assertEqual("abcd", new_update_action["someprop"])
        
        # and there are new ones
        self.assertEqual("efgh", case["somenewprop"])
        self.assertEqual("efgh", new_update_action["somenewprop"])
        
        # we also changed everything originally in the case
        self.assertEqual("a_new_type", case.type)
        self.assertEqual("a_new_type", new_update_action.type)
        self.assertEqual("a new name", case.name)
        self.assertEqual("a new name", new_update_action.name)        
        self.assertEqual(UPDATE_DATE, case.opened_on)
        self.assertEqual(UPDATE_DATE, new_update_action.opened_on)
        
        # case should have a new modified date
        self.assertEqual(MODIFY_DATE, case.modified_on)
        
        self.assertEqual(0, len(case.referrals))
    
    def testCreateThenClose(self):
        case = self._bootstrap_case_from_xml("create.xml")
        case.save()
                
        # now close it
        case = self._bootstrap_case_from_xml("close.xml", case.case_id)
        self.assertEqual(True, case.closed)
        
        self.assertEqual(3, len(case.actions))
        update_action = case.actions[1]
        close_action = case.actions[2]
        self.assertEqual(const.CASE_ACTION_UPDATE, update_action.action_type)
        self.assertEqual(const.CASE_ACTION_CLOSE, close_action.action_type)
        
        self.assertEqual("abcde", case["someprop"])
        self.assertEqual("abcde", update_action["someprop"])
        self.assertEqual("case closed", case["someclosedprop"])
        self.assertEqual("case closed", update_action["someclosedprop"])
        
        self.assertEqual(CLOSE_DATE, close_action.date)
        self.assertEqual(CLOSE_DATE, case.modified_on)
        self.assertEqual(0, len(case.referrals))
        
    def testCreateMultiple(self):
        # TODO: test creating multiple cases from a single form
        pass
    
    def testCreateAndUpdateInDifferentCaseBlocks(self):
        # TODO: two case blocks, one that creates, another that updates
        pass
    
    def testReferrals(self):
        case = self._bootstrap_case_from_xml("create.xml")
        case.save()
        self.assertEqual(0, len(case.referrals))
        case = self._bootstrap_case_from_xml("open_referral.xml", case.case_id)
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.actions))
        self.assertEqual(2, len(case.referrals))
        for referral in case.referrals:
            self.assertTrue(referral.type in ("t1", "t2"))
            self.assertEqual(False, referral.closed)
            self.assertEqual(REFER_DATE, referral.followup_on)
            self.assertEqual(case.modified_on, referral.modified_on)
            self.assertEqual(case.modified_on, referral.opened_on)
         
    
    def _check_static_properties(self, case):
        self.assertEqual("test_case_type", case.type)
        self.assertEqual("test case name", case.name)
        self.assertEqual("someuser", case.user_id)
        self.assertEqual(ORIGINAL_DATE, case.opened_on)
        self.assertEqual(ORIGINAL_DATE, case.modified_on)
        self.assertEqual("someexternal", case.external_id)

    def _bootstrap_case_from_xml(self, filename, case_id=None):
        file_path = os.path.join(os.path.dirname(__file__), "data", filename)
        xml_data = open(file_path, "rb").read()
        doc_id, uid, case_id, ref_id = _replace_ids_and_post(xml_data, case_id_override=case_id)  
        cases_touched = get_or_update_cases(CXFormInstance.get_db().get(doc_id))
        self.assertEqual(1, len(cases_touched))
        case = cases_touched[case_id]
        self.assertEqual(case_id, case.case_id)
        return case
            

        
def _replace_ids_and_post(xml_data, case_id_override=None):
    # from our test forms, replace the UIDs so we don't get id conflicts
    uid, case_id, ref_id = (uuid.uuid4().hex for i in range(3))
    
    if case_id_override:
        case_id = case_id_override
    xml_data = xml_data.replace("REPLACE_UID", uid)
    xml_data = xml_data.replace("REPLACE_CASEID", case_id)
    xml_data = xml_data.replace("REPLACE_REFID", ref_id)
    doc_id, _ = post_data(xml_data, settings.XFORMS_POST_URL )
    return (doc_id, uid, case_id, ref_id)
    
    