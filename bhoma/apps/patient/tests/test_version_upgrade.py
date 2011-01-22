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
        self.assertEqual(settings.BHOMA_APP_VERSION, patient.original_app_version)
        
    def testIsCurrent(self):
        patient = random_person()
        patient.app_version = MIN_VERSION
        patient.save()
        self.assertEqual(MIN_VERSION, patient.app_version)
        self.assertFalse(patient.is_current())
        patient = random_person()
        patient.app_version = settings.BHOMA_APP_VERSION
        patient.save()
        self.assertTrue(patient.is_current())
        patient = random_person()
        patient.app_version = MAX_VERSION
        patient.save()
        # even though it's from the future, it's still not current.
        self.assertFalse(patient.is_current())
        
                
    def testReprocessUpgradesVersion(self):
        patient = random_person()
        patient.app_version = MIN_VERSION
        patient.save()
        self.assertEqual(MIN_VERSION, patient.app_version)
        self.assertEqual(MIN_VERSION, patient.original_app_version)
        reprocess(patient.get_id)
        patback = CPatient.get(patient.get_id)
        self.assertEqual(settings.BHOMA_APP_VERSION, patback.app_version)
        # shouldn't upgrade the original version
        self.assertEqual(MIN_VERSION, patient.original_app_version)
    
    def testEmptyVersionRequiresUpgrade(self):
        patient = random_person()
        patient.app_version = None
        self.assertTrue(patient.requires_upgrade())
        
    def testVersionUpgradeOnlyDependsOnFirstTwoDigits(self):
        old_ver = settings.BHOMA_APP_VERSION 
        settings.BHOMA_APP_VERSION = "0.1.5"
        patient = random_person()
        patient.app_version = "0.1.0"
        self.assertFalse(patient.requires_upgrade())
        patient.app_version = "0.1.5"
        self.assertFalse(patient.requires_upgrade())
        patient.app_version = "0.1.9"
        self.assertFalse(patient.requires_upgrade())
        patient.app_version = "0.1.4.2"
        self.assertFalse(patient.requires_upgrade())
        patient.app_version = "0.0.9"
        self.assertTrue(patient.requires_upgrade())
        patient.app_version = "0.2.0"
        self.assertFalse(patient.requires_upgrade())
        settings.BHOMA_APP_VERSION = old_ver