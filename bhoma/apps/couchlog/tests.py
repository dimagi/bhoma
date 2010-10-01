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
    
    def testExtraInfo(self):
        self.assertEqual(0, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        try:
            raise Exception("Fail!")
        except Exception:
            log_exception(extra_info="Uber failure!")
        self.assertEqual(1, len(ExceptionRecord.view("couchlog/all_by_date").all()))
        log = ExceptionRecord.view("couchlog/all_by_date").one()
        self.assertEqual("Uber failure!", log.extra_info)