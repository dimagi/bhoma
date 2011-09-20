from django.test import TestCase
from bhoma.apps.case.bhomacaselogic.random import predictable_random
from dimagi.utils.couch import uid

class RandomFollowupTest(TestCase):
    
    def testRandomFunction(self):
        # since this is a random statistical test there is a chance
        # it could readily fail. The threshold was chosen to be 
        # what seems to be well out of normal range of firing, but
        # in randomness anything is possible.
        test_size = 100000
        threshold = .002 
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
                    
            
            