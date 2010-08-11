import os
from datetime import date
from django.conf import settings
from django.test import TestCase
from bhoma.utils.post import post_authenticated_data
from bhoma.apps.xforms.models.couch import CXFormInstance

class TestMeta(TestCase):
    
    def testClosed(self):
        file_path = os.path.join(os.path.dirname(__file__), "data", "meta.xml")
        xml_data = open(file_path, "rb").read()
        doc_id, errors = post_authenticated_data(xml_data, 
                                                 settings.XFORMS_POST_URL, 
                                                 settings.BHOMA_COUCH_USERNAME,
                                                 settings.BHOMA_COUCH_PASSWORD)
        xform = CXFormInstance.get(doc_id)
        self.assertNotEqual(None, xform.metadata)
        self.assertEqual("5020280", xform.metadata.clinic_id)
        self.assertEqual(date(2010,07,22), xform.metadata.time_start.date())
        self.assertEqual(date(2010,07,23), xform.metadata.time_end.date())
        self.assertEqual("admin", xform.metadata.username)
        self.assertEqual("f7f0c79e-8b79-11df-b7de-005056c00008", xform.metadata.user_id)
        