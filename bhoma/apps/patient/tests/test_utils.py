from django.test import TestCase
from datetime import datetime
from dimagi.utils.parsing import string_to_datetime

class UtilsTestCase(TestCase):
    
    def testDateParsing(self):
        self.assertEqual(datetime(2010,01,15), string_to_datetime("2010-01-15"))