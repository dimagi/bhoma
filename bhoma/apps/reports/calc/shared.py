from bhoma.utils.couch import safe_index
from datetime import timedelta

"""Module for shared code used in reports"""
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import first_visit_data

def encounter_in_range(encounter, date, delta=timedelta(days=3)):
    return date - delta <= encounter.visit_date <= date + delta
         
        
###################   pregnancy section   ###################

def get_hiv_result(healthy_visit):
    hiv = safe_index(healthy_visit, ["hiv_first_visit", "hiv"])
    if hiv:  return hiv
    hiv = safe_index(healthy_visit, ["hiv_after_first_visit", "hiv"])
    if hiv:  return hiv
    return None
        
def tested_positive(visit_data):
    hiv = get_hiv_result(visit_data)
    if hiv is not None:
        if first_visit_data(visit_data): return hiv == "prev_r" or hiv == "r"
        else:                            return hiv == "r"
    return False

