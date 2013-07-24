from django.test import TestCase
import os
from datetime import date
from bhoma.apps.patient import export

class DeliveryTest(TestCase):
    
    def testBasicDelivery(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "delivery_case_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))

        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))

        [delivery] = updated_patient.deliveries
        self.assertEqual(date(2013, 7, 24), delivery.delivery_date)
        self.assertFalse(delivery.closed)