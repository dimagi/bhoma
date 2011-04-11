from django.test import TestCase
from datetime import datetime
from dimagi.utils.parsing import string_to_datetime

class UtilsTestCase(TestCase):
    
    def testDateParsing(self):
        self.assertEqual(datetime(1965,7,20), string_to_datetime("1965-07-20"))