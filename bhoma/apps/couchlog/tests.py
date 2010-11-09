from django.test import TestCase
from bhoma.utils.data import random_person
from django.conf import settings
from bhoma.apps.patient.processing import reprocess
from bhoma.apps.patient.models.couch import CPatient
from bhoma.utils.logging import log_exception
from bhoma.apps.couchlog.models import ExceptionRecord

class LogTestCase(TestCase):
    
    def setUp(self):
        for item in ExceptionRecord.view("couchlog/all_by_date").all():
            item.delete()
    
    def testCreation(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        try:
            raise Exception("Fail!")
        except Exception:
            log_exception()
        self.assertEqual(1, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        log = ExceptionRecord.view("couchlog/all_by_date").one()
        self.assertEqual("Fail!", log.message)
        self.assertTrue("tests.py" in log.stack_trace)
        self.assertFalse(log.archived)
        
    def testSettingsInfo(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        try:
            raise Exception("Fail!")
        except Exception:
            log_exception()
        log = ExceptionRecord.view("couchlog/all_by_date").one()
        self.assertEqual(settings.BHOMA_APP_VERSION, log.app_version)
        self.assertEqual(settings.BHOMA_COMMIT_ID, log.commit_id)
        
    def testExtraInfo(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        try:
            raise Exception("Fail!")
        except Exception:
            log_exception(extra_info="Uber failure!")
        self.assertEqual(1, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        log = ExceptionRecord.view("couchlog/all_by_date").one()
        self.assertEqual("Uber failure!", log.extra_info)