from django.test import TestCase
from datetime import date
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line,\
    check_commcare_dates
from bhoma.apps.case.const import Outcome
from bhoma.apps.phone.models import PhoneCase

class AdultVisitTest(TestCase):
    
    def testLostNotSentToPhone(self):
        """
        Creates a case that is too long ago and is lost and checks that it's flagged
        as "over" and therefore won't go to the phone.
        """
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "ltfu_test")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, form_doc1 = export.add_form_file_to_patient(patient.get_id, os.path.join(folder_name, "001_general.xml"))
        [case] = updated_patient.cases
        case.patient = updated_patient
        phone_case = PhoneCase.from_bhoma_case(case)
        self.assertTrue(phone_case.is_over(date(2011, 01, 01)))
        