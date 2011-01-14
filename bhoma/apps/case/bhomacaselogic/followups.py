
"""Operations related to followups go here."""
from bhoma.apps.case import const
from bhoma.utils.dates import safe_date_add
from bhoma.utils.mixins import UnicodeMixIn
from bhoma.apps.patient.encounters.config import SICK_PREGNANCY_SLUG,\
    DELIVERY_SLUG

class FollowupType(UnicodeMixIn):
    """
    An object representing how to follow up on a bhoma visit
    """
     
    CLOSE = 0
    REFERRAL = 1
    FACILITY = 2
    DEATH = 3
    BLANK = 4 # data entry system marked it blank
    EMPTY = 5 # there was actually no value in the form (bad data)
    
    # when they entered something that shouldn't have been entered, 
    # e.g. "death" and "facility"
    ILLEGAL_STATE = 6
    BAD_VALUE = 7 # something that was unexpected
    
    def __init__(self, type, values):
        self._type = type
        self._values = values

    @property
    def type(self):
        return self._type
    
    @property
    def values(self):
        return self._values
    
    def __unicode__(self):
        return "%s: %s" % (self.type, ", ".join(self.values))
    
    def _fail(self):
        raise NotImplementedError("This method should be overridden!")
    
    def is_valid(self):
        self._fail()
        
    def closes_case(self):
        self._fail()
        
    def get_status(self):
        self._fail()
        
    def get_outcome(self):
        self._fail()
        
    def get_phone_followup_type(self):
        self._fail()
        
    def get_activation_date(self, open_date):
        self._fail()
        
    def get_start_date(self, open_date):
        self._fail()
        
    def get_due_date(self, open_date):
        self._fail()
        
    def get_missed_appointment_date(self, open_date):
        self._fail()
    
    def get_ltfu_date(self, open_date):
        self._fail()
    
    @classmethod
    def type_from_value(cls, value):
        # I find this branching style to be more readable, though it could be
        # argued both ways
        if not value:                                     return FollowupType.EMPTY
        elif const.FOLLOWUP_TYPE_BLANK == value:          return FollowupType.BLANK
        elif const.FOLLOWUP_TYPE_CLOSE == value:          return FollowupType.CLOSE
        elif const.FOLLOWUP_TYPE_DEATH == value \
          or const.FOLLOWUP_TYPE_MATERNAL_DEATH == value: return FollowupType.DEATH
        elif const.FOLLOWUP_TYPE_REFER == value:          return FollowupType.REFERRAL
        elif const.FOLLOWUP_TYPE_FOLLOW_CLINIC == value:  return FollowupType.FACILITY
        # note that while neonatal death is actually a possible value here, it
        # should always be part of a compound value and is thus, bad.
        else:                                             return FollowupType.BAD_VALUE
            
    @classmethod
    def get_primary_type(cls, values):
        valid_outcomes = [const.FOLLOWUP_TYPE_CLOSE, 
                          const.FOLLOWUP_TYPE_DEATH,
                          const.FOLLOWUP_TYPE_MATERNAL_DEATH,
                          const.FOLLOWUP_TYPE_REFER,
                          const.FOLLOWUP_TYPE_FOLLOW_CLINIC]
        found_outcome = None
        for candidate in valid_outcomes:
            if candidate in values: 
                if found_outcome is None:
                    found_outcome = candidate
                else: 
                    # if there's more than one primary outcome
                    # it's an illegal state
                    return FollowupType.ILLEGAL_STATE
        
        if found_outcome is None:
            # if we didn't find any valid primary outcome it's an illegal state
            return FollowupType.ILLEGAL_STATE
        else:
            return FollowupType.type_from_value(found_outcome)
        
    @classmethod
    def type_from_values(cls, values):
        if not values:
            return FollowupType.EMPTY
        
        # base case:
        if len(values) == 1:
            return FollowupType.type_from_value(values[0])
        else:
            return FollowupType.get_primary_type(values)

class ValidFollowupType(FollowupType):
    def is_valid(self):         return True
    
class InvalidFollowupType(FollowupType):
    def is_valid(self):         return False
    
class FollowupClose(ValidFollowupType):
    def closes_case(self):      return True
    def get_outcome(self):      return const.Outcome.CLOSED_AT_CLINIC
     
class FollowupDeath(ValidFollowupType):
    def closes_case(self):      return True
    def get_outcome(self):      return const.Outcome.PATIENT_DIED
    
class FollowupReferral(ValidFollowupType):
    def closes_case(self):                  return False
    def get_status(self):                   return const.Status.REFERRED
    def get_phone_followup_type(self):      return const.PHONE_FOLLOWUP_TYPE_HOSPITAL
    
    def get_activation_date(self, open_date):
        return safe_date_add(open_date, 14)
    
    def get_start_date(self, open_date):
        return safe_date_add(open_date, 9)
    
    def get_due_date(self, open_date):
        return safe_date_add(open_date, 19)
        
    def get_ltfu_date(self, open_date):
        return safe_date_add(open_date, 42)
        
    def get_missed_appointment_date(self, open_date):
        return None
    
class FollowupFacility(ValidFollowupType):
    
    DEFAULT_DAYS = 5 # if the date is not specified, when to default to
    
    def __init__(self, type, values, days):
        super(FollowupFacility, self).__init__(type, values)
        if days is not None:
            self._days = days
        else: 
            self._days = FollowupFacility.DEFAULT_DAYS
    
    def closes_case(self):                  return False
    def get_status(self):                   return const.Status.RETURN_TO_CLINIC
    def get_phone_followup_type(self):      return const.PHONE_FOLLOWUP_TYPE_MISSED_APPT
    
    def get_activation_date(self, open_date):
        return safe_date_add(self.get_missed_appointment_date(open_date), 3)
    
    def get_start_date(self, open_date):
        return safe_date_add(self.get_missed_appointment_date(open_date), 3)
    
    def get_due_date(self, open_date):
        return safe_date_add(self.get_missed_appointment_date(open_date), 13)
    
    def get_ltfu_date(self, open_date):
        return safe_date_add(open_date, 42)
    
    def get_missed_appointment_date(self, open_date):
        return safe_date_add(open_date, self._days)
    
    
class FollowupBlank(ValidFollowupType):
    # For the time being we decide that blank cases should still be followed 
    # up on by the chw 
    def closes_case(self):                  return False
    def get_status(self):                   return const.Status.CHW_FOLLOW_UP
    def get_phone_followup_type(self):      return const.PHONE_FOLLOWUP_TYPE_CHW
     
    def get_activation_date(self, open_date):
        return safe_date_add(open_date, 8)
    
    def get_start_date(self, open_date):
        return safe_date_add(open_date, 8)
    
    def get_due_date(self, open_date):
        return safe_date_add(open_date, 18)
    
    def get_ltfu_date(self, open_date):
        return safe_date_add(open_date, 42)
    
    def get_missed_appointment_date(self, open_date):
        return None
    
def get_followup_type(xform):
    """From a bhoma xform, get the followup type."""
    
    case_block = xform.xpath(const.CASE_TAG)
    if case_block:
        if const.FOLLOWUP_TYPE_TAG not in case_block or \
                case_block[const.FOLLOWUP_TYPE_TAG] is None:
            return FollowupType([])
        
        # some forms can have more than one followup type, which 
        # in the xform look like a space-separated list
        followup_values = case_block[const.FOLLOWUP_TYPE_TAG].split(" ")
        type = FollowupType.type_from_values(followup_values)
        if   type == FollowupType.CLOSE:    return FollowupClose(type, followup_values)
        elif type == FollowupType.REFERRAL: return FollowupReferral(type, followup_values)
        # facility follow up is more complicated, also needs to know the # days 
        # from the case block
        elif type == FollowupType.FACILITY:
            follow_days = None
            if const.FOLLOWUP_DATE_TAG in case_block:
                try:
                    follow_days = int(case_block[const.FOLLOWUP_DATE_TAG])
                except ValueError:   pass
            return FollowupFacility(type, followup_values, follow_days)
        elif type == FollowupType.DEATH:    return FollowupDeath(type, followup_values)
        elif type == FollowupType.BLANK:    return FollowupBlank(type, followup_values)
        elif type == FollowupType.EMPTY or \
             type == FollowupType.ILLEGAL_STATE or \
             type == FollowupType.BAD_VALUE:
                                            return InvalidFollowupType(type, followup_values)
        
        raise Exception("The followup type of %s is not supported.  Values are %s" % (type, ", ".join(values)))


# since these don't actually have values they're different from followuptype 
# above, but they still live here.

class PregnancyFollowup():
    def __init__(self, close, outcome):
        self._close = close
        self._outcome = outcome
    
    def closes_case(self):
        return self._close
    
    def get_outcome(self):
        return self._outcome
    
def get_pregnancy_followup(encounter):
    """Whether an encounter closes a pregnancy"""
    # there are only a few conditions that close a pregnancy case.
    # 1. Sick pregnancy visit or delivery resulting in mother and/or fetal death
    if encounter.type == SICK_PREGNANCY_SLUG or encounter.type == DELIVERY_SLUG:
        case_outcome = encounter.get_xform().xpath("case/followup_type")
        if case_outcome:
            if const.FOLLOWUP_TYPE_MATERNAL_DEATH in case_outcome:
                return PregnancyFollowup(True, const.Outcome.PATIENT_DIED)
            elif const.FOLLOWUP_TYPE_FETAL_DEATH in case_outcome:
                return PregnancyFollowup(True, const.Outcome.FETAL_DEATH)
    if encounter.type == DELIVERY_SLUG:
        # 2. Delivery form that results in birth
        delivery_entered = encounter.get_xform().xpath("continue_form") == "y"
        if delivery_entered:
            return PregnancyFollowup(True, const.Outcome.BIRTH)
    return PregnancyFollowup(False, "N/A")
    
