from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_pregnancy_encounter,\
    get_edd, lmp_from_edd
from datetime import timedelta
import logging

DAYS_BEFORE_LMP_START = 7 # how many days before lmp do we match encounters
DAYS_AFTER_EDD_END = 56 # how many days after edd do we match encounters (8 wks)

class RepartitionException(Exception):
    pass

   
def update_pregnancies(patient, encounter):
    """
    From a patient object, update the list of pregnancies.
    """
    if is_pregnancy_encounter(encounter):
        
        # by default we create a new pregnancy unless we find a match 
        matched_pregnancy = None
        if len(patient.pregnancies) > 0:
            potential_match = patient.pregnancies[-1]
            if _is_match(potential_match, encounter):
                matched_pregnancy = potential_match
        if matched_pregnancy:
            matched_pregnancy.add_visit(encounter)
            
        else:
            # recursive import :(
            from bhoma.apps.case.models.couch import Pregnancy
            preg = Pregnancy.from_encounter(encounter)
            patient.pregnancies.append(preg)
            
    return patient
    

def _is_match(potential_match, encounter):
    """
    Whether a pregnancy matches an encounter.
    """
    # if it's open and the visit is before the end date it's a clear match
    if potential_match.is_open() and potential_match.get_end_date() > encounter.visit_date:
        return True
    # if it's closed, but was only closed in the last two weeks it's a match
    elif not potential_match.is_open() and \
         potential_match.end_date() + timedelta(14) > encounter.visit_date:
        return True
    elif potential_match.pregnancy_dates_set():
        # the dates were set and we didn't match.  no match.
        return False
    else:
        # if the dates weren't set, cross check against _our_ dates
        edd = get_edd(encounter)
        if edd:
            end_date = edd + timedelta(days=DAYS_AFTER_EDD_END)
            start_date = lmp_from_edd(edd) - timedelta(days=DAYS_BEFORE_LMP_START)
            if start_date < potential_match.get_first_visit_date() < end_date and \
               start_date < potential_match.get_last_visit_date() < end_date:
                return True
            elif start_date < potential_match.get_first_visit_date() < end_date or \
                 start_date < potential_match.get_last_visit_date() < end_date:
                # what to do about this corner case?  Half the visits fall in
                # the other half don't. 
                # just add it for now
                logging.error("Pregnancy dates out of whack for visit, trying our best "
                              "to deal with it (xform: %s)" % encounter.get_xform().get_id)
                return True
            else:
                # dates clearly not in range
                return False
        else:
            # if the visit date is < 9 months (270 days) from the first known 
            # visit date, count it
            return potential_match.get_first_visit_date() < encounter.visit_date < potential_match.get_first_visit_date() + timedelta(days=270)
