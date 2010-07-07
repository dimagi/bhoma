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
from bhoma.utils.data import random_person
from bhoma.apps.case.tests.test_const import *
from bhoma.apps.patient.models import CPatient
from bhoma.apps.case.tests.util import bootstrap_case_from_xml

class CaseInPatientTest(TestCase):
    
    def testCreate(self):
        patient = random_person()
        case = bootstrap_case_from_xml(self, "create.xml")
        patient.cases=[case,]
        patient.save()
        # make sure we can get it back from our shared view
        case_back = CCase.get_with_patient(case.case_id)
        self.assertEqual(case.case_id, case_back.case_id)
        self.assertEqual(patient.first_name, case_back.patient.first_name)
        self.assertEqual(patient.last_name, case_back.patient.last_name)
        self.assertEqual(patient.get_id, case_back.patient.get_id)
        self.assertEqual(1, len(patient.cases))
        self.assertEqual(case.case_id, patient.cases[0].case_id)
        
        
    def testUpdate(self):
        patient = random_person()
        case = bootstrap_case_from_xml(self, "create_update.xml")
        patient.cases=[case,]
        patient.save()
        # make sure we can get it back from our shared view
        case_back = CCase.get_with_patient(case.case_id)
        self.assertEqual(case.case_id, case_back.case_id)
        self.assertEqual(patient.first_name, case_back.patient.first_name)
        self.assertEqual(patient.last_name, case_back.patient.last_name)
        self.assertEqual(patient.get_id, case_back.patient.get_id)
        self.assertEqual(1, len(patient.cases))
        self.assertEqual(case.case_id, patient.cases[0].case_id)
        
        # update
        case = bootstrap_case_from_xml(self, "update.xml", case.case_id)
        self.assertEqual(patient.get_id, case.patient.get_id)
        case.save()
        
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.cases))
        case_in_patient = patient.cases[0]
        self.assertEqual(case.case_id, case_in_patient.case_id)
        
        self.assertEqual(False, case_in_patient.closed)
        self.assertEqual(3, len(case_in_patient.actions))
        new_update_action = case_in_patient.actions[2]
        self.assertEqual(const.CASE_ACTION_UPDATE, new_update_action.action_type)
        
        # some properties didn't change
        self.assertEqual("123", str(case["someotherprop"]))
        
        # but some should have
        self.assertEqual("abcd", case_in_patient["someprop"])
        self.assertEqual("abcd", new_update_action["someprop"])
        
        # and there are new ones
        self.assertEqual("efgh", case_in_patient["somenewprop"])
        self.assertEqual("efgh", new_update_action["somenewprop"])
        
        # we also changed everything originally in the case
        self.assertEqual("a_new_type", case_in_patient.type)
        self.assertEqual("a_new_type", new_update_action.type)
        self.assertEqual("a new name", case_in_patient.name)
        self.assertEqual("a new name", new_update_action.name)        
        self.assertEqual(UPDATE_DATE, case_in_patient.opened_on)
        self.assertEqual(UPDATE_DATE, new_update_action.opened_on)
        
        # case should have a new modified date
        self.assertEqual(MODIFY_DATE, case.modified_on)
        
    def testReferralClose(self):
        patient = random_person()
        case = bootstrap_case_from_xml(self, "create.xml")
        patient.cases=[case,]
        patient.save()
        case = bootstrap_case_from_xml(self, "open_referral.xml", case.case_id)
        case.save()
        case = bootstrap_case_from_xml(self, "close_referral.xml", case.case_id, case.referrals[0].referral_id)
        case.save()
        patient = CPatient.get(patient.get_id)
        print patient.get_id
        case = patient.cases[0]
        self.assertEqual(False, case.closed)
        self.assertEqual(1, len(case.actions))
        self.assertEqual(2, len(case.referrals))
        self.assertEqual(MODIFY_2_DATE, case.modified_on)
        for referral in case.referrals:
            if referral.type == "t1":
                self.assertEqual(True, referral.closed)
                self.assertEqual(REFER_DATE, referral.followup_on)
                self.assertEqual(case.modified_on, referral.modified_on)
                self.assertEqual(MODIFY_DATE, referral.opened_on)
            elif referral.type == "t2":
                self.assertEqual(False, referral.closed)
                self.assertEqual(REFER_DATE, referral.followup_on)
                self.assertEqual(MODIFY_DATE, referral.modified_on)
                self.assertEqual(MODIFY_DATE, referral.opened_on)
            else:
                self.fail("Unexpected referral type %s!" % referral.type)
    