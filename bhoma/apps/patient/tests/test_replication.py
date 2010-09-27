from django.test import TestCase
from django.conf import settings
from couchdbkit import *
from bhoma.utils.data import random_person
from couchdbkit.ext.django.forms import document_to_dict
from bhoma.apps.patient.models.couch import CPatient
import os
from couchdbkit.loaders import FileSystemDocLoader
from bhoma.utils.couch import delete
from bhoma.utils.couch.sync import replicate
from bhoma import const
from bhoma.utils.couch.database import get_db

TEST_CLINIC_1 = "test_clinic_1"
TEST_CLINIC_2 = "test_clinic_2"
TEST_NATIONAL = "test_national"

class ReplicationTest(TestCase):
    
    def setUp(self):
        server = get_db().server
        self.databases = [TEST_CLINIC_1, TEST_CLINIC_2, TEST_NATIONAL]
        
        # cleanup
        for database in self.databases:
            try:                 delete(server, database)
            except Exception, e: print e
        
        # create databases
        self.clinic_1_db = server.get_or_create_db(TEST_CLINIC_1)
        self.clinic_2_db = server.get_or_create_db(TEST_CLINIC_2)
        self.national_db = server.get_or_create_db(TEST_NATIONAL)
        
        # load design docs
        design_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                     "patient", "models")
        loader = FileSystemDocLoader(design_path, "_design", design_name="patient")
        for database in [self.clinic_1_db, self.clinic_2_db, self.national_db]:
            loader.sync(database, verbose=True)

        self.server = server
        
    def testFullPushReplication(self):
        self.assertEqual(0, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self._add_patients(self.clinic_1_db, 100)
        self.assertEqual(100, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self.assertEqual(0, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        self.server.replicate(TEST_CLINIC_1, TEST_NATIONAL)
        self.assertEqual(100, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        
    def testDualPushReplication(self):
        
        self.assertEqual(0, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self._add_patients(self.clinic_1_db, 100)
        self.assertEqual(100, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self._add_patients(self.clinic_2_db, 100)
        self.assertEqual(100, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self.server.replicate(TEST_CLINIC_1, TEST_NATIONAL)
        self.assertEqual(100, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self.server.replicate(TEST_CLINIC_2, TEST_NATIONAL)
        self.assertEqual(200, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self.assertEqual(100, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(100, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        
        
        
    def testSelectivePullReplication(self):
        """
        Create national patients with different clinic ids and make sure they
        get selectively replicated to the proper clinics
        """
        self.assertEqual(0, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        self._add_patients(self.national_db, 10, TEST_CLINIC_1)
        self._add_patients(self.national_db, 20, TEST_CLINIC_2)
        self._add_patients(self.national_db, 30)
        
        self.assertEqual(0, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(60, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        # replicate to clinic 1
        replicate(self.server, TEST_NATIONAL, TEST_CLINIC_1, 
                  filter=const.FILTER_CLINIC, 
                  query_params={ const.PROPERTY_CLINIC_ID: TEST_CLINIC_1 })
        
        self.assertEqual(10, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(0, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(60, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
        # replicate to clinic 2
        replicate(self.server, TEST_NATIONAL, TEST_CLINIC_2, 
                  filter=const.FILTER_CLINIC, 
                  query_params={ const.PROPERTY_CLINIC_ID: TEST_CLINIC_2 })
        
        self.assertEqual(10, self.clinic_1_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(20, self.clinic_2_db.view(const.VIEW_ALL_PATIENTS).count())
        self.assertEqual(60, self.national_db.view(const.VIEW_ALL_PATIENTS).count())
        
           
        
    def _add_patients(self, database, count, clinic_id=None):
        """Adds <count> random patients to <database>"""
        # if we don't specify a clinic, use the database name
        if clinic_id is None:  clinic_id = database.dbname
        CPatient.set_db(database)
        for i in range(count):
            p = random_person()
            p.clinic_ids = [clinic_id,]
            p.save()
        
        