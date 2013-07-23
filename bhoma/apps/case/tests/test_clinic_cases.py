from django.test import TestCase
from datetime import datetime, timedelta
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line,\
    add_form_with_date_offset
from bhoma.apps.case.const import Outcome

class ClinicCaseTest(TestCase):
    
    def testClosedCases(self):
        # run through all four forms, verify that the case closed at the clinic
        # behaves properly
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "closed_cases")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertEqual("tb", case.type)
        self.assertEqual(Outcome.CLOSED_AT_CLINIC, case.outcome)
        self.assertEqual(0, len(case.commcare_cases))
        
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_sick_pregnancy.xml"))
        [_, case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertEqual("malaria", case.type)
        self.assertEqual(Outcome.CLOSED_AT_CLINIC, case.outcome)
        self.assertEqual(0, len(case.commcare_cases))
    
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_underfive.xml"))
        [_, _, case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertEqual("meningitis", case.type)
        self.assertEqual(Outcome.CLOSED_AT_CLINIC, case.outcome)
        self.assertEqual(0, len(case.commcare_cases))

    
    def testMissedAppointmentPhoneCase(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "phone_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "001_general.xml"),
                 days_from_today=-1)

        
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[0]
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        self.assertEqual("diarrhea", case.type)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual(None, case.outcome)
        
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        today = datetime.utcnow().date()
        visit_date = today + timedelta(days=-1)
        start_date = visit_date + timedelta(days=7)
        due_date = start_date + timedelta(days=10)
        self.assertEqual(start_date, ccase.activation_date)
        self.assertEqual(due_date, ccase.due_date)
        self.assertEqual(start_date, ccase.start_date)
        
        # grab the case xml and check it against what we expect to get back
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[updated_patient.get_id]))
        
        expected_casexml = \
"""<cases>
<case>
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
        <age>%(age)s</age>
        <sex>f</sex>
        <village>GSMLAND</village>
        <contact>0128674102</contact>
        <bhoma_case_id>61a91e70d246486b99abb6ad752e82a5</bhoma_case_id>
        <bhoma_patient_id>829684277b127eed27e1d6ef08d6c74a</bhoma_patient_id>
        <followup_type>missed_appt</followup_type>
        <orig_visit_type>general</orig_visit_type>
        <orig_visit_diagnosis>diarrhea</orig_visit_diagnosis>
        <orig_visit_date>%(visit_date)s</orig_visit_date>
        <activation_date>%(start)s</activation_date>
        <due_date>%(due)s</due_date>
        <missed_appt_date>%(missed)s</missed_appt_date>
    </update>
</case>
</cases>""" % {"today": date_to_xml_string(today),
               "visit_date": date_to_xml_string(visit_date),
               "age": updated_patient.formatted_age,
               "start": date_to_xml_string(start_date),
               "due": date_to_xml_string(due_date),
               "missed": date_to_xml_string(start_date - timedelta(days=3))}
        
        check_xml_line_by_line(self, expected_casexml, response.content)
        
        # add the phone followup
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "002_chw_fu.xml"),
                 days_from_today=0)
                
        self.assertEqual(1, len(updated_patient.cases))
        [case] = updated_patient.cases
        self.assertTrue(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        self.assertEqual("diarrhea", case.type)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("lost_to_followup_wont_return_to_clinic", case.outcome)
        
        
    def _run_phone_visit_case_test(self, folder_name, type):
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        #  a. Severe symptom
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_%s.xml" % type))
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertTrue("severe_symptom_checked" in case.send_to_phone_reason)
        
        #  b. Danger sign
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_%s.xml" % type))
        self.assertEqual(2, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("danger_sign_present", case.send_to_phone_reason)
        
        #  c. Missed appointment < 5 days
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_%s.xml" % type))
        self.assertEqual(3, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        
        #  d. None of the above (no case)
        updated_patient, form_doc4 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "004_%s.xml" % type))
        self.assertEqual(4, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.send_to_phone)
        self.assertEqual("sending_criteria_not_met", case.send_to_phone_reason)
                
    def testGeneralVisitPhoneCaseGeneration(self):
        
        # General visit
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "general_visit")
        self._run_phone_visit_case_test(folder_name, "general")
        
    
    def testUnderFivePhoneCaseGeneration(self):
        
        # Under five visit
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "under_five")
        self._run_phone_visit_case_test(folder_name, "underfive")
        
    
    def testDeliveryPhoneCaseGeneration(self):
        # Delivery
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "delivery_tester")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        #  a. Missed appointment < 5 days
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        
        #  b. None of the above (no case)
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_delivery.xml"))
        self.assertEqual(2, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.send_to_phone)
        self.assertEqual("sending_criteria_not_met", case.send_to_phone_reason)
        
        
    def testSickPregnancyPhoneCaseGeneration(self):
        # Sick pregnancy
        
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "sick_pregnancy")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        # forms are loaded one at a time.  If you need to run tests at 
        # intermediate states, put them in between whatever forms you
        # want loaded

        #  a. Severe symptom
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_sick_pregnancy.xml"))
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertTrue("severe_symptom_checked" in case.send_to_phone_reason)
        
        #  b. Missed appointment < 5 days
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_sick_pregnancy.xml"))
        self.assertEqual(2, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("urgent_clinic_followup", case.send_to_phone_reason)
        
        #  c. None of the above (no case)
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_sick_pregnancy.xml"))
        self.assertEqual(3, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.send_to_phone)
        self.assertEqual("sending_criteria_not_met", case.send_to_phone_reason)

    
    def testHealthyPregnancyPhoneCaseGeneration(self):
        # Healthy Pregnancy
        #  a. initial visit creates case for N days past EDD
         
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "healthy_pregnancy")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        # forms are loaded one at a time.  If you need to run tests at 
        # intermediate states, put them in between whatever forms you
        # want loaded
        days_offset = -50
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"),
                 days_from_today=days_offset)

        
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("pregnancy_expecting_outcome", case.send_to_phone_reason)
        [ccase] = case.commcare_cases
        self.assertEqual("pregnancy", ccase.followup_type)
        self.assertFalse(ccase.closed)
        today = datetime.utcnow().date()
        visit_date = today + timedelta(days=days_offset)
        start_date = visit_date + timedelta(days=7*42)
        ltfu_date = visit_date + timedelta(days=7*46)
        due_date = start_date + timedelta(days=5)
        #self.assertEqual(visit_date, ccase.visit_date)
        self.assertEqual(start_date, ccase.start_date)
        self.assertEqual(start_date, ccase.activation_date)
        self.assertEqual(due_date, ccase.due_date)
        self.assertEqual(ltfu_date, case.ltfu_date)
        self.assertEqual("pregnancy|pregnancy", ccase.name)
        
        
    def testMissedApptBug(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "missedappt_bug")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "001_underfive.xml"),
                 days_from_today=0)

        today = datetime.utcnow().date()
        # grab the case xml and check it against what we expect to get back
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[updated_patient.get_id]))
        expected_xml = \
"""<cases>
<case>
    <case_id>ef17b25547da4554842100e3e3eb3fb7</case_id> 
    <date_modified>%(today)s</date_modified>
    <create>
        <case_type_id>bhoma_followup</case_type_id> 
        <user_id>a014b648-9bed-11df-a250-0001c006087d</user_id> 
        <case_name>underfive</case_name> 
        <external_id>9cfaf4cf2abb411ba7ca0593293109fc</external_id>
    </create>
    <update>
        <first_name>MISSEDAPP</first_name>
        <last_name>BUG</last_name>
        <birth_date>2008-07-20</birth_date>
        <birth_date_est>False</birth_date_est>
        <age>%(age)s</age>
        <sex>f</sex>
        <village>FOX</village>
        <contact>8569</contact>
        <bhoma_case_id>9cfaf4cf2abb411ba7ca0593293109fc</bhoma_case_id>
        <bhoma_patient_id>42253e98d9b241fe7b28a2e3da1f0dbd</bhoma_patient_id>
        <followup_type>hospital</followup_type>
        <orig_visit_type>underfive</orig_visit_type>
        <orig_visit_diagnosis></orig_visit_diagnosis>
        <orig_visit_date>%(today)s</orig_visit_date>
        <activation_date>%(active)s</activation_date>
        <due_date>%(due)s</due_date>
        <missed_appt_date></missed_appt_date>
    </update>
</case>
</cases>""" % {"today": date_to_xml_string(datetime.utcnow().date()),
               "age": updated_patient.formatted_age,
               "active": date_to_xml_string(today + timedelta(days=14)),
               "due": date_to_xml_string(today + timedelta(days=19))}
        
        check_xml_line_by_line(self, expected_xml, response.content)
        
    def testHugeFollow(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "huge_follow")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # these all have huge follow up dates, so these functions not throwing errors
        # is enough to test.
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_sick_pregnancy.xml"))
            
