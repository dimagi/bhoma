from django.test import TestCase
from datetime import date, datetime
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line

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
        
    def testPhoneTest(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "phone_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        # forms are loaded one at a time.  If you need to run tests at 
        # intermediate states, put them in between whatever forms you
        # want loaded

        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[0]
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        self.assertEqual(date(2010, 9, 9), ccase.activation_date)
        self.assertEqual(date(2010, 9, 16), ccase.due_date)
        self.assertEqual(date(2010, 9, 9), ccase.start_date)
        
        # grab the case xml and check it against what we expect to get back
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[updated_patient.get_id]))
        
        expected_casexml = \
"""<case>
    <case_id>27e45e6086a8418290f82e1494ca54e7</case_id> 
    <date_modified>%(today)s</date_modified>
    <create>
        <case_type_id>bhoma_followup</case_type_id> 
        <user_id>f4374680-9bea-11df-a4f6-005056c00008</user_id> 
        <case_name>general|diarrhea</case_name> 
        <external_id>61a91e70d246486b99abb6ad752e82a5</external_id>
    </create>
    <update>
        <first_name>PHONE</first_name>
        <last_name>TEST</last_name>
        <birth_date>1987-03-19</birth_date>
        <birth_date_est>False</birth_date_est>
        <age>23</age>
        <sex>f</sex>
        <village>GSMLAND</village>
        <contact>0128674102</contact>
        <bhoma_case_id>829684277b127eed27e1d6ef08d6c74a</bhoma_case_id>
        <bhoma_patient_id>829684277b127eed27e1d6ef08d6c74a</bhoma_patient_id>
        <followup_type>missed_appt</followup_type>
        <orig_visit_type>general</orig_visit_type>
        <orig_visit_diagnosis>diarrhea</orig_visit_diagnosis>
        <orig_visit_date>2010-09-01</orig_visit_date>
        <activation_date>2010-09-09</activation_date>
        <due_date>2010-09-16</due_date>
        <missed_appt_date>2010-09-06</missed_appt_date>
    </update>
</case>""" % {"today": date_to_xml_string(date.today())}
        
        check_xml_line_by_line(self, expected_casexml, response.content)        