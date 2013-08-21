from django.test import TestCase
import os
from datetime import datetime, timedelta
from bhoma.apps.case import const
from bhoma.apps.case.tests.util import add_form_with_date_offset
from bhoma.apps.patient import export

class DeliveryTest(TestCase):

    def setUp(self):
        self.folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "delivery_case_test")
        patient = export.import_patient_json_file(os.path.join(self.folder_name, "patient.json"))
        self.patient, self.delivery_form = add_form_with_date_offset(
            patient.get_id, os.path.join(self.folder_name, "001_delivery.xml")
        )

    def tearDown(self):
        self.patient.delete()
        self.delivery_form.delete()

    def testBasicDelivery(self):
        today = datetime.utcnow().date()
        [delivery] = self.patient.deliveries
        self.assertEqual(self.delivery_form._id, delivery.xform_id)
        self.assertEqual(today, delivery.date)
        self.assertFalse(delivery.closed)
        _, delivery_case = self.patient.cases

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

        fu1, fu2 = delivery_case.commcare_cases
        test_dates(fu1, 4, 6, 16, 26)
        test_dates(fu2, 23, 28, 33, 70)

    def testFUBabyDied(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_baby_died.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertTrue(delivery_case.closed)
        self.assertEqual('postnatal_followup_completed', delivery_case.outcome)

        # should close the other follow up too
        self.assertTrue(fu1.closed)
        self.assertTrue(fu2.closed)

        # self.assertEqual('n', delivery_case.baby_alive)
        # self.assertEqual('anaemia', delivery_case.baby_cause_of_death)


    def testFUMotherDied(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_mother_died.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertTrue(delivery_case.closed)
        self.assertEqual('died', delivery_case.outcome)
        # self.assertEqual('n', delivery_case.mother_alive)
        # self.assertEqual('meteor', delivery_case.mother_cause_of_death)

        self.assertTrue(fu1.closed)
        self.assertTrue(fu2.closed)

    def testFUNormalVisit1(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_normal_visit1.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertFalse(delivery_case.closed)
        self.assertEqual(None, delivery_case.outcome)

        self.assertTrue(fu1.closed)
        self.assertFalse(fu2.closed)

    def testFU_LTFU1(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_ltfu1.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertFalse(delivery_case.closed)
        self.assertEqual(None, delivery_case.outcome)

        self.assertTrue(fu1.closed)
        self.assertFalse(fu2.closed)

    def testFU_LTFU(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_ltfu2.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertTrue(delivery_case.closed)
        self.assertEqual('lost_to_followup_time_window', delivery_case.outcome)

        # should close the other follow up too
        self.assertTrue(fu1.closed)
        self.assertTrue(fu2.closed)

    def testFUNoVisit(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_no_visit.xml",
            case_id=fu1._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertFalse(delivery_case.closed)
        self.assertEqual(None, delivery_case.outcome)

        # should close the other follow up too
        self.assertFalse(fu1.closed)
        self.assertFalse(fu2.closed)

    def testFURiskFactors(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_risk_factors.xml",
            case_id=fu1._id,
        )

        # todo: should this actually close the bhoma case?
        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertTrue(delivery_case.closed)
        self.assertEqual('referred_back_to_clinic', delivery_case.outcome)
        self.assertEqual('y', delivery_case.baby_alive)

        # should close the other follow up too
        self.assertTrue(fu1.closed)
        self.assertTrue(fu2.closed)

    def testFUComplete(self):
        _, delivery_case = self.patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        updated_patient, fu_form = self._add_form(
            "chw_fu_second_visit_ok.xml",
            case_id=fu2._id,
        )

        _, delivery_case = updated_patient.cases
        fu1, fu2 = delivery_case.commcare_cases
        self.assertTrue(delivery_case.closed)
        self.assertEqual('postnatal_followup_completed', delivery_case.outcome)

        self.assertTrue(fu1.closed)
        self.assertTrue(fu2.closed)

    def _add_form(self, form_name, **kwargs):
        with open(os.path.join(self.folder_name, form_name)) as f:
            date_string = datetime.utcnow().date().strftime("%Y-%m-%d")
            form = f.read().format(
                date=date_string,
                patient_id=self.patient._id,
                **kwargs
            )
            return export.add_form_to_patient(self.patient._id, form)