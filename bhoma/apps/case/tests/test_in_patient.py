import os
import uuid
import tempfile
from datetime import datetime
from django.test import TestCase
from django.conf import settings
from bhoma.apps.xforms.models import XForm
from bhoma.apps.case.models import CommCareCase
from dimagi.utils.post import post_file, post_data
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
        case_back = CommCareCase.get_with_patient("case/all_and_patient", case.case_id)
        self.assertEqual(case.case_id, case_back.case_id)
        self.assertEqual(patient.first_name, case_back.patient.first_name)
        self.assertEqual(patient.last_name, case_back.patient.last_name)
        self.assertEqual(patient.get_id, case_back.patient.get_id)
        self.assertEqual(1, len(patient.cases))
        self.assertEqual(case._id, patient.cases[0]._id)
        
        
    def testUpdate(self):
        patient = random_person()
        case = bootstrap_case_from_xml(self, "create_update.xml")
        patient.cases=[case,]
        patient.save()
        # make sure we can get it back from our shared view
        case_back = CommCareCase.get_with_patient("case/all_and_patient", case.case_id)
        self.assertEqual(case.case_id, case_back.case_id)
        self.assertEqual(patient.first_name, case_back.patient.first_name)
        self.assertEqual(patient.last_name, case_back.patient.last_name)
        self.assertEqual(patient.get_id, case_back.patient.get_id)
        self.assertEqual(1, len(patient.cases))
        self.assertEqual(case._id, patient.cases[0]._id)
        
        # update
        case = bootstrap_case_from_xml(self, "update.xml", case.case_id)
        self.assertEqual(patient.get_id, case.patient.get_id)
        case.save()
        
        patient = CPatient.get(patient.get_id)
        self.assertEqual(1, len(patient.cases))
        case_in_patient = patient.cases[0]
        self.assertEqual(case._id, case_in_patient._id)
        
        self.assertEqual(False, case_in_patient.closed)
        self.assertEqual(3, len(case_in_patient.actions))
        new_update_action = case_in_patient.actions[2]
        self.assertEqual(const.CASE_ACTION_UPDATE, new_update_action["action_type"])
        
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
        self.assertEqual("a_new_type", new_update_action["type"])
        self.assertEqual("a new name", case_in_patient.name)
        self.assertEqual("a new name", new_update_action["name"])        
        self.assertEqual(UPDATE_DATE, case_in_patient.opened_on)
        self.assertEqual(UPDATE_DATE, new_update_action["opened_on"])
        
        # case should have a new modified date
        self.assertEqual(MODIFY_DATE, case.modified_on)
        
