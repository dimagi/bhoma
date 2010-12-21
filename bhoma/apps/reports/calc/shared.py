from bhoma.utils.couch import safe_index
from datetime import timedelta

"""Module for shared code used in reports"""
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import first_visit_data
import logging

def encounter_in_range(encounter, date, delta=timedelta(days=3)):
    return date - delta <= encounter.visit_date <= date + delta
         
        
###################   pregnancy section   ###################

def get_hiv_result(healthy_visit):
    hiv = safe_index(healthy_visit, ["hiv_result"])
    if hiv:  return hiv
    return None
        
def tested_positive(visit_data):
    logging.error("examine this merge conflict more carefully!!!")
    hiv = get_hiv_result(visit_data)
    if hiv is not None:
        # pregnancy branch code
        #if first_visit_data(visit_data): return hiv == "prev_r" or hiv == "r"
        #else:                            return hiv == "r"
        return hiv == "r"
    return False

def not_on_haart(visit_data):
    haart = safe_index(visit_data, ["on_haart"])
    if haart is not None:
        return haart == "n"
    return False

