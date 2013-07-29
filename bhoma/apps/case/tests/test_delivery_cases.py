from django.test import TestCase
import os
from datetime import date
from bhoma.apps.case import const
from bhoma.apps.patient import export

class DeliveryTest(TestCase):
    
    def testBasicDelivery(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "delivery_case_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))

        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))

        [delivery] = updated_patient.deliveries
        self.assertEqual(form_doc1._id, delivery.xform_id)
        self.assertEqual(date(2013, 7, 24), delivery.date)
        self.assertFalse(delivery.closed)
        _, delivery_case = updated_patient.cases

        self.assertFalse(delivery_case.closed)
        self.assertEqual(const.CASE_TYPE_DELIVERY, delivery_case.type)
