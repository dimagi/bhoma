from bhoma.utils.couch import safe_index

"""Module for shared code used in reports"""

###################   pregnancy section   ###################

def is_first_visit(form):
    return hasattr(form, "first_visit")


def get_hiv_result(healthy_visit):
    if safe_index(healthy_visit, ["hiv_first_visit", "hiv"]):
        return healthy_visit.hiv_first_visit.hiv
    elif safe_index(healthy_visit, ["hiv_after_first_visit", "hiv"]):
        return healthy_visit.hiv_after_first_visit.hiv
        
def tested_positive(visit_data):
    hiv = get_hiv_result(visit_data)
    if hiv is not None:
        if is_first_visit(visit_data): return hiv == "prev_r" or hiv == "r"
        else:                          return hiv == "r"
    return False

