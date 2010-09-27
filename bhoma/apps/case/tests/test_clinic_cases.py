from django.test import TestCase
from datetime import date, datetime
from bhoma.apps.patient import export as export
import os

class ClinicCaseTest(TestCase):

    def testBasicClinicCases(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "clinic_case")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # test a case that immediately closes
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[0]
        self.assertTrue(case.closed)
        self.assertEqual("other_infection", case.type)
        self.assertEqual("closed at clinic", case.status)
        self.assertEqual("injuries_treated", case.outcome)
        
        # test a follow with chw case
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        self.assertEqual(2, len(updated_patient.cases))
        case = updated_patient.cases[1]
        self.assertFalse(case.closed)
        self.assertEqual("tb", case.type)
        self.assertEqual("followup with chw", case.status)
        self.assertEqual("", case.outcome)
        self.assertFalse(case.send_to_phone)
        self.assertEqual(datetime(2010, 9, 5), case.opened_on)
        self.assertEqual(date.today(), case.modified_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("chw", ccase.followup_type)
        self.assertEqual(date(2010, 9, 10), ccase.activation_date)
        self.assertEqual(date(2010, 9, 17), ccase.due_date)
        self.assertEqual(date(2010, 9, 7), ccase.start_date)
        
        # test a refer to hospital case
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_general.xml"))
        self.assertEqual(3, len(updated_patient.cases))
        # old case should be closed
        old_case = updated_patient.cases[1]
        self.assertTrue(old_case.closed)
        self.assertEqual("tb", old_case.type)
        self.assertEqual("followup with chw", old_case.status)
        self.assertEqual("returned_to_clinic", old_case.outcome)
        
        case = updated_patient.cases[2]
        self.assertFalse(case.closed)
        self.assertEqual("hypertension", case.type)
        self.assertEqual("referred", case.status)
        self.assertEqual("", case.outcome)
        self.assertFalse(case.send_to_phone)
        self.assertEqual(datetime(2010, 9, 14), case.opened_on)
        self.assertEqual(date.today(), case.modified_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("hospital", ccase.followup_type)
        self.assertEqual(date(2010, 9, 26), ccase.activation_date)
        self.assertEqual(date(2010, 10, 3), ccase.due_date)
        self.assertEqual(date(2010, 9, 23), ccase.start_date)
        
        # test a return to clinic case
        updated_patient, form_doc4 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "004_general.xml"))
        self.assertEqual(4, len(updated_patient.cases))
        
        # old case should be closed
        old_case = updated_patient.cases[2]
        self.assertTrue(old_case.closed)
        self.assertEqual("hypertension", case.type)
        self.assertEqual("referred", case.status)
        self.assertEqual("returned_to_clinic", old_case.outcome)
        
        case = updated_patient.cases[3]
        self.assertFalse(case.closed)
        self.assertEqual("other", case.type)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("", case.outcome)
        self.assertFalse(case.send_to_phone)
        self.assertEqual(datetime(2010, 9, 17), case.opened_on)
        self.assertEqual(date.today(), case.modified_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        self.assertEqual(date(2010, 9, 27), ccase.activation_date)
        self.assertEqual(date(2010, 10, 4), ccase.due_date)
        self.assertEqual(date(2010, 9, 27), ccase.start_date)
        
