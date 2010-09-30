from bhoma.apps.patient.encounters import config
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_pregnancy_encounter,\
    get_edd, lmp_from_edd, first_visit_data
from datetime import timedelta
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.utils.parsing import string_to_datetime
import logging
from bhoma.apps.case.models.couch import CPregnancy

DAYS_BEFORE_LMP_START = 7 # how many days before lmp do we match encounters
DAYS_AFTER_EDD_END = 56 # how many days after edd do we match encounters (8 wks)

class PregnancyDatesNotSetException(Exception):
    pass

class RepartitionException(Exception):
    pass

class Pregnancy(UnicodeMixIn):
    """
    Data that encapsulates a pregnancy.  Consists of a group of pregnancy 
    encounters that link together to form a single object.
    """
    
    def __init__(self):
        self.edd = None
        self._first_visit = None
        self._encounters = []
        self._open = True

    def __unicode__(self):
        return "Pregancy: (due: %s)" % (self.edd)
    
    def is_open(self):
        return self._open
    
    def pregnancy_dates_set(self):
        return self.edd is not None
    
    
    @property
    def lmp(self):
        if self.edd:
            return lmp_from_edd(self.edd)
        raise PregnancyDatesNotSetException()
    
    def get_first_visit_date(self):
        return self.sorted_encounters()[0].visit_date
    
    def get_last_visit_date(self):
        return self.sorted_encounters()[-1].visit_date
    
    def get_start_date(self):
        if self.pregnancy_dates_set():
            return self.lmp - timedelta(days=DAYS_BEFORE_LMP_START)
        return self.get_first_visit_date()
        
    def get_end_date(self):
        if self.pregnancy_dates_set():
            return self.edd + timedelta(days=DAYS_AFTER_EDD_END)
        return self.get_last_visit_date()
    
    def sorted_encounters(self):
        return sorted(self._encounters, key=lambda encounter: encounter.visit_date)
    
    def to_couch_object(self):
        first_encounter_id = self._first_visit.get_id if self._first_visit else ""
        return CPregnancy(edd=self.edd,
                          first_encounter_id=first_encounter_id,
                          encounter_ids=[e.get_id for e in self.sorted_encounters()])
    
    @classmethod
    def from_encounter(cls, encounter):
        preg = Pregnancy()
        preg.add_visit(encounter)
        return preg
        
    def add_visit(self, encounter):
        # adds data from a visit
        self._encounters.append(encounter)
        edd = get_edd(encounter)
        first_visit = first_visit_data(encounter.get_xform())
        if not self.pregnancy_dates_set() and edd:
            self.edd = edd
        if not self._first_visit and first_visit:
            self._first_visit = encounter
    
def update_pregnancies(patient):
    """
    From a patient object, update the list of pregnancies.
    """
    pregs = extract_pregnancies(patient)
    patient.pregnancies = [preg.to_couch_object() for preg in pregs]
    for preg in pregs:
        #print preg
        pass
    return patient
    
def extract_pregnancies(patient):
    """
    From a patient object, extract a list of pregnancies.
    """
    pregs = []
    for encounter in sorted(patient.encounters, key=lambda enc: enc.visit_date):
        if is_pregnancy_encounter(encounter):
            # find a matching pregnancy
            found_preg = None
            if len(pregs) == 0:
                pregs.append(Pregnancy.from_encounter(encounter))
            else:
                # since we're going through encounters in chronological order 
                # we can assume that the only possible match is the most recent
                # pregnancy
                potential_match = pregs[-1]
                if _is_match(potential_match, encounter):
                    potential_match.add_visit(encounter)
                else:
                    # we have to create a new pregnancy for this. 
                    found_preg = Pregnancy.from_encounter(encounter)
                    pregs.append(found_preg)
    return pregs

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
