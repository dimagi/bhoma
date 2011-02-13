import os
from datetime import date
from django.conf import settings
from django.test import TestCase
from dimagi.utils.post import post_authenticated_data
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.xforms.util import post_xform_to_couch, post_from_settings

class LockTest(TestCase):
    
    def testPostCreatesLock(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "meta.xml")
        with open(file_path, "rb") as f:
            xml_data = f.read()
        doc_id, errors = post_from_settings(xml_data)
        xform = CXFormInstance.get(doc_id)
        self.assertTrue(xform.is_locked())
        
    def testUtilityReleasesLock(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "meta.xml")
        with open(file_path, "rb") as f:
            xml_data = f.read()
        doc = post_xform_to_couch(xml_data)
        self.assertFalse(doc.is_locked())
        