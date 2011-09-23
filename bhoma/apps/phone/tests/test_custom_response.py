from django.test import TestCase
from django.test.client import Client
from datetime import datetime, timedelta
import os
from bhoma.apps.phone.xml import date_to_xml_string
from dimagi.utils.couch import uid

class CustomResponseTest(TestCase):
    
    def testCustomResponse(self):
        template_file = os.path.join(os.path.dirname(__file__), "data", "referral.xml")
        with open(template_file) as f:
            template = f.read()
        
        c = Client()
        
        now = datetime.now().date()
        def _post_and_confirm(form, count):
            response = c.post("/phone/post/", data=form, content_type="text/xml")
            self.assertEqual(200, response.status_code)
            self.assertTrue(("<FormsSubmittedToday>%s</FormsSubmittedToday>" % count) in response.content)
            self.assertTrue(("<TotalFormsSubmitted>%s</TotalFormsSubmitted>" % count) in response.content)
        
        
        for i in range(5):
            form = template % {"date": date_to_xml_string(now),
                               "uid": uid.new()}
            _post_and_confirm(form, i + 1)

        for i in range(5):
            # make sure past submissions also show up as today
            form = template % {"date": date_to_xml_string(now - timedelta(days=i)),
                               "uid": uid.new()}
            _post_and_confirm(form, i + 6)