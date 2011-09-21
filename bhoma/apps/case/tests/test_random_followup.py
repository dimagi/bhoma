from django.test import TestCase
from bhoma.apps.case.bhomacaselogic.random import predictable_random
from dimagi.utils.couch import uid
from bhoma.apps.case import const
import os
from bhoma.apps.patient import export
from bhoma.apps.case.tests.util import add_form_with_date_offset,\
    check_commcare_dates

class RandomFollowupTest(TestCase):
    
    def setUp(self):
        super(RandomFollowupTest, self).setUp()
        # in this test, make sure the random follow up always fires
        self.previous_probability = const.AUTO_FU_PROBABILITY 
        const.AUTO_FU_PROBABILITY = 1.0
        
    def tearDown(self):
        # leave no trace
        const.AUTO_FU_PROBABILITY = self.previous_probability
        super(RandomFollowupTest, self).tearDown()
        
    def testRandomFunction(self):
        # since this is a random statistical test there is a chance
        # it could readily fail. The threshold was chosen to be 
        # what seems to be well out of normal range of firing, but
        # in randomness anything is possible.
        test_size = 100000
        threshold = .003
        probabilities = [0, 0.02, .5, .9, 1]
        for probability in probabilities:
            truecount = 0
            falsecount = 0
            while truecount + falsecount < test_size:
                if predictable_random(uid.new(), probability):
                    truecount += 1
                else:
                    falsecount += 1
            
            calculated_probability = (float(truecount) / float(test_size))
            self.assertTrue(probability - threshold < calculated_probability)
            self.assertTrue(probability + threshold > calculated_probability)
                    
    def _checkRandomFollowup(self, case):
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertEqual(const.SendToPhoneReasons.RANDOMLY_CHOSEN, 
                         case.send_to_phone_reason)
        [ccase] = case.commcare_cases
        check_commcare_dates(self, case, ccase, 9, 14, 19, 42)
        
        
    def testCloseStaysOpen(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "random_futest")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "001_general.xml"),
                 days_from_today=0)

        [case] = updated_patient.cases
        self._checkRandomFollowup(case)
        
                
    def testNonSevereGoesToPhone(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "random_futest")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "002_general.xml"),
                 days_from_today=0)
        [case] = updated_patient.cases
        self._checkRandomFollowup(case)        
                
    def testSevereUnchanged(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "random_futest")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "003_general.xml"),
                 days_from_today=0)
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertNotEqual(const.SendToPhoneReasons.RANDOMLY_CHOSEN, 
                            case.send_to_phone_reason)
        [ccase] = case.commcare_cases
        # these dates are different because it should actually
        # follow the original cases logic, in this case a missed
        # appointment 7 days later
        check_commcare_dates(self, case, ccase, 10, 10, 20, 42)
             
        
    def testPregnancyUnchanged(self):
        folder_name = os.path.join(os.path.dirname(__file__), "testpatients", "random_futest")
        patient = export.import_patient_json_file(os.path.join(folder_name, "patient.json"))
        updated_patient, _ = add_form_with_date_offset\
                (patient.get_id, os.path.join(folder_name, "004_pregnancy.xml"),
                 days_from_today=0)
        [case] = updated_patient.cases
        self.assertFalse(case.closed)
        self.assertTrue(case.send_to_phone)
        self.assertNotEqual(const.SendToPhoneReasons.RANDOMLY_CHOSEN, 
                            case.send_to_phone_reason)
        [ccase] = case.commcare_cases
        # use the pregnancy dates
        check_commcare_dates(self, case, ccase, 7*42, 7*42, 7*42+5, 7*46)
        
        
        