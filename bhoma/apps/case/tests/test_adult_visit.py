from django.test import TestCase
from datetime import date, datetime
from bhoma.apps.patient import export as export
from django.test.client import Client
import os
from django.core.urlresolvers import reverse
from bhoma.apps.phone.xml import date_to_xml_string
from bhoma.apps.case.tests.util import check_xml_line_by_line,\
    check_commcare_dates, add_form_with_date_offset
from bhoma.apps.case.const import Outcome

class AdultVisitTest(TestCase):
    
    def testCaseOutcomes(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "adult_visit")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        
        # Enter new form, make sure to choose a danger sign, then choose outcome follow up prn
        updated_patient, form_doc1 = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "001_general.xml"),
                 days_from_today=-5)

        [case] = updated_patient.cases
        self.assertFalse(patient.is_deceased)
        self.assertEqual(0, len(case.commcare_cases))
        self.assertTrue(case.closed)
        self.assertEqual(Outcome.CLOSED_AT_CLINIC, case.outcome)
        
        # Enter new form, make sure to choose a danger sign, then choose outcome referred
        updated_patient, form_doc2 = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "002_general.xml"),
                 days_from_today=-4)
        self.assertEqual(2, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.closed)
        [ccase] = case.commcare_cases
        check_commcare_dates(self, case, ccase, 9, 14, 19, 42)
        
        # Enter new form, make sure to choose a danger sign, then choose outcome follow up facilility
        updated_patient, form_doc3 = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "003_general.xml"),
                 days_from_today=-3)

        self.assertEqual(3, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.closed)
        [ccase] = case.commcare_cases
        check_commcare_dates(self, case, ccase, 10, 10, 20, 42)
        
        # Enter new form, make sure to choose a danger sign, then choose outcome blank
        updated_patient, form_doc4 = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "004_general.xml"),
                 days_from_today=-2)

        self.assertEqual(4, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertFalse(case.closed)
        [ccase] = case.commcare_cases
        check_commcare_dates(self, case, ccase, 8, 8, 18, 42)
        
        # Enter new form, make sure to choose a danger sign, then choose outcome death
        updated_patient, form_doc5 = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "005_general.xml"),
                 days_from_today=-1)
                
        self.assertEqual(5, len(updated_patient.cases))
        case = updated_patient.cases[-1]
        self.assertTrue(case.closed)
        self.assertEqual(0, len(case.commcare_cases))
        self.assertTrue(updated_patient.is_deceased)
        