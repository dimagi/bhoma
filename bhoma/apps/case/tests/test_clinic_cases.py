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
        [ccase] = case.commcare_cases
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
        self.assertEqual("hypertension", old_case.type)
        self.assertEqual("referred", old_case.status)
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
        
        # test a "none" case
        updated_patient, form_doc5 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "005_general.xml"))
        self.assertEqual(5, len(updated_patient.cases))
        
        # old case should be closed
        old_case = updated_patient.cases[3]
        self.assertTrue(old_case.closed)
        self.assertEqual("other", old_case.type)
        self.assertEqual("return to clinic", old_case.status)
        self.assertEqual("returned_to_clinic", old_case.outcome)
        
        case = updated_patient.cases[4]
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual(datetime(2010, 9, 19), case.opened_on)
        self.assertEqual(date.today(), case.modified_on.date())
        self.assertEqual(1, len(case.commcare_cases))
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("chw", ccase.followup_type)
        self.assertEqual(date(2010, 9, 26), ccase.activation_date)
        self.assertEqual(date(2010, 10, 3), ccase.due_date)
        self.assertEqual(date(2010, 9, 23), ccase.start_date)
        
        
    def testMissedAppointmentPhoneCase(self):
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
        self.assertEqual("diarrhea", case.type)
        self.assertEqual("return to clinic", case.status)
        self.assertEqual("", case.outcome)
        
        ccase = case.commcare_cases[0]
        self.assertFalse(ccase.closed)
        self.assertEqual(case.get_id, ccase.external_id)
        self.assertEqual("missed_appt", ccase.followup_type)
        self.assertEqual(date(2010, 9, 8), ccase.activation_date)
        self.assertEqual(date(2010, 9, 15), ccase.due_date)
        self.assertEqual(date(2010, 9, 8), ccase.start_date)
        
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
        <bhoma_case_id>61a91e70d246486b99abb6ad752e82a5</bhoma_case_id>
        <bhoma_patient_id>829684277b127eed27e1d6ef08d6c74a</bhoma_patient_id>
        <followup_type>missed_appt</followup_type>
        <orig_visit_type>general</orig_visit_type>
        <orig_visit_diagnosis>diarrhea</orig_visit_diagnosis>
        <orig_visit_date>2010-09-01</orig_visit_date>
        <activation_date>2010-09-08</activation_date>
        <due_date>2010-09-15</due_date>
        <missed_appt_date>2010-09-05</missed_appt_date>
    </update>
</case>""" % {"today": date_to_xml_string(date.today())}
        
        check_xml_line_by_line(self, expected_casexml, response.content)
        
        # add the phone followup
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_chw_fu.xml"))
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
        self.assertEqual("severe_symptom_checked", case.send_to_phone_reason)
        
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
        self.assertEqual("severe_symptom_checked", case.send_to_phone_reason)
        
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

        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_pregnancy.xml"))
        
        self.assertEqual(1, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.send_to_phone)
        self.assertEqual("pregnancy_expecting_outcome", case.send_to_phone_reason)
        [ccase] = case.commcare_cases
        self.assertEqual("pregnancy", ccase.followup_type)
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[updated_patient.get_id]))
        
        expected_xml = \
"""<case>
    <case_id>5f6600492327495ab6d75bd0c7b08dd4</case_id> 
    <date_modified>%(today)s</date_modified>
    <create>
        <case_type_id>bhoma_followup</case_type_id> 
        <user_id>f4374680-9bea-11df-a4f6-005056c00008</user_id> 
        <case_name>pregnancy|pregnancy</case_name> 
        <external_id>012cd69b213f4e2b98aef39f510420be</external_id>
    </create>
    <update>
        <first_name>HEALTHY</first_name>
        <last_name>PREGNANCY</last_name>
        <birth_date>1982-06-17</birth_date>
        <birth_date_est>False</birth_date_est>
        <age>28</age>
        <sex>f</sex>
        <village>OOO</village>
        <contact>42</contact>
        <bhoma_case_id>012cd69b213f4e2b98aef39f510420be</bhoma_case_id>
        <bhoma_patient_id>2d47191385f72dc86b6a41272408160c</bhoma_patient_id>
        <followup_type>pregnancy</followup_type>
        <orig_visit_type>pregnancy</orig_visit_type>
        <orig_visit_diagnosis>pregnancy</orig_visit_diagnosis>
        <orig_visit_date>2010-09-01</orig_visit_date>
        <activation_date>2011-02-15</activation_date>
        <due_date>2011-02-20</due_date>
        <missed_appt_date>2011-02-15</missed_appt_date>
    </update>
</case>""" % {"today": date_to_xml_string(date.today())}

        check_xml_line_by_line(self, expected_xml, response.content)
        
        
    def testMissedApptBug(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "missedappt_bug")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        updated_patient, form_doc4 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_underfive.xml"))
        
        # grab the case xml and check it against what we expect to get back
        c = Client()
        response = c.get(reverse("patient_case_xml", args=[updated_patient.get_id]))
        expected_xml = \
"""<case>
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
        <age>2 yrs, 3 mos</age>
        <sex>f</sex>
        <village>FOX</village>
        <contact>8569</contact>
        <bhoma_case_id>9cfaf4cf2abb411ba7ca0593293109fc</bhoma_case_id>
        <bhoma_patient_id>42253e98d9b241fe7b28a2e3da1f0dbd</bhoma_patient_id>
        <followup_type>hospital</followup_type>
        <orig_visit_type>underfive</orig_visit_type>
        <orig_visit_diagnosis></orig_visit_diagnosis>
        <orig_visit_date>2010-09-02</orig_visit_date>
        <activation_date>2010-09-14</activation_date>
        <due_date>2010-09-21</due_date>
        <missed_appt_date></missed_appt_date>
    </update>
</case>""" % {"today": date_to_xml_string(date.today())}
        
        check_xml_line_by_line(self, expected_xml, response.content)
        
    def testHugeFollow(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "huge_follow")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # these all have huge follow up dates, so these functions not throwing errors
        # is enough to test.
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_delivery.xml"))
        updated_patient, form_doc2 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "002_general.xml"))
        updated_patient, form_doc3 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "003_sick_pregnancy.xml"))
            