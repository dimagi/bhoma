from dimagi.utils.couch import safe_index
from datetime import timedelta

"""Module for shared code used in reports"""

def encounter_in_range(encounter, date, delta=timedelta(days=3)):
    return date - delta <= encounter.visit_date <= date + delta
         
        
###################   pregnancy section   ###################

def get_hiv_result(healthy_visit):
    hiv = safe_index(healthy_visit, ["hiv_result"])
    if hiv:  return hiv
    return None
        
def tested_positive(visit_data):
    """
    This tests whether the patient tested positive on a particular visit.
    It does not indicate if they have ever tested positive previously.
    """
    hiv = get_hiv_result(visit_data)
    if hiv is not None:
        # pregnancy branch code
        return hiv == "r"
    return False

def not_on_haart(visit_data):
    haart = safe_index(visit_data, ["on_haart"])
    if haart is not None:
        return haart == "n"
    return False

