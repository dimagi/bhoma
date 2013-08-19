from django.test import TestCase
import os
from datetime import date, datetime, timedelta
from bhoma.apps.case import const
from bhoma.apps.case.tests.util import add_form_with_date_offset
from bhoma.apps.patient import export

class DeliveryTest(TestCase):
    
    def testBasicDelivery(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "delivery_case_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))

        updated_patient, form_doc1 = add_form_with_date_offset(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))

        today = datetime.utcnow().date()
        [delivery] = updated_patient.deliveries
        self.assertEqual(form_doc1._id, delivery.xform_id)
        self.assertEqual(today, delivery.date)
        self.assertFalse(delivery.closed)
        _, delivery_case = updated_patient.cases

        self.assertFalse(delivery_case.closed)
        self.assertEqual(const.CASE_TYPE_DELIVERY, delivery_case.type)

        self.assertEqual(2, len(delivery_case.commcare_cases))
        for ccase in delivery_case.commcare_cases:
            self.assertEqual(const.PHONE_FOLLOWUP_TYPE_DELIVERY, ccase.followup_type)
            self.assertFalse(ccase.closed)
            self.assertEqual("delivery|delivery", ccase.name)
            self.assertTrue(ccase.visit_number in ('1', '2'))

        def test_dates(ccase, start_offset, active_offset, due_offset, ltfu_offset):
            self.assertEqual(today + timedelta(days=start_offset), ccase.start_date)
            self.assertEqual(today + timedelta(days=active_offset), ccase.activation_date)
            self.assertEqual(today + timedelta(days=due_offset), ccase.due_date)
            self.assertEqual(today + timedelta(days=ltfu_offset), ccase.ltfu_date)

        [fu1, fu2] = delivery_case.commcare_cases
        test_dates(fu1, 4, 6, 16, 26)
        test_dates(fu2, 23, 28, 33, 70)

