from django.test import TestCase
from django.conf import settings
from dimagi.utils.logging import log_exception
from couchlog.models import ExceptionRecord
import logging

class BhomaLogTestCase(TestCase):
    
    def setUp(self):
        for item in ExceptionRecord.view("couchlog/all_by_date", include_docs=True).all():
            item.delete()
    
    def testSettingsInfo(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date", include_docs=True).all()))
        try:
            raise Exception("Fail!")
        except Exception, e:
            logging.exception(e)
        log = ExceptionRecord.view("couchlog/all_by_date", include_docs=True).one()
        self.assertEqual(settings.APP_VERSION, log.app_version)
        self.assertEqual(settings.BHOMA_COMMIT_ID, log.commit_id)
        
    