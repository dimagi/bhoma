from django.test import TestCase
from bhoma.utils.data import random_person
from django.conf import settings
from bhoma.apps.patient.processing import reprocess
from bhoma.apps.patient.models.couch import CPatient

MIN_VERSION = "0.0.0"
MAX_VERSION = "999.99.99"
        
class VersionTestCase(TestCase):
    
    def testVersionNumberSet(self):
        patient = random_person()
        patient.save()
        self.assertEqual(settings.BHOMA_APP_VERSION, patient.app_version)
                
    def testReprocessUpgradesVersion(self):
        patient = random_person()
        patient.app_version = MIN_VERSION
        patient.save()
        self.assertEqual(MIN_VERSION, patient.app_version)
        reprocess(patient.get_id)
        patback = CPatient.get(patient.get_id)
        self.assertEqual(settings.BHOMA_APP_VERSION, patback.app_version)
        