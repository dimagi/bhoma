"""
Bhoma-specific utility methods for cases.  TODO: abstract / move this somewhere more
appropriate. 
"""

from datetime import datetime, time, timedelta
from bhoma.apps.case import const
from bhoma.apps.case.models import CommCareCase
from bhoma.utils import parsing
from bhoma.apps.case.models import CommCareCaseAction
from bhoma.apps.patient.models import CPatient
from bhoma.utils.couch import uid
from bhoma.apps.case.models.couch import PatientCase
from bhoma.utils.parsing import string_to_datetime
from bhoma.apps.case.bhomacaselogic import *
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS,\
    HEALTHY_PREGNANCY_NAMESPACE
from bhoma.apps.case.pregnancylogic import get_pregnancy_outcome
from bhoma.utils.logging import log_exception
from bhoma.apps.case.exceptions import CaseLogicException
    

def close_previous_cases(patient, form, encounter):
    """
    From the patient, find any open missed appointment (or pending appointment) 
    cases and close them.
    """
    pregnancy_outcome = get_pregnancy_outcome(form)
    for case in patient.cases:
        if not case.closed and case.opened_on.date() < encounter.visit_date:
            if case.type == const.CASE_TYPE_PREGNANCY:
                # pregnancy cases only get closed if there was a pregnancy outcome
                if pregnancy_outcome:
                    close_case(case, encounter, pregnancy_outcome)
            else:
                close_case(case, encounter, const.OUTCOME_RETURNED_TO_CLINIC)
    patient.save()
                    
                    

def get_or_update_bhoma_case(xformdoc, encounter):
    """
    Process Bhoma XML - which looks like this:
        <case>
            <patient_id></patient_id> <!-- patient -->
            <case_type></case_type> <!-- diagnosis -->
            <followup_type></followup_type> <!-- referral, chw followup, facility followup, closed -->
            <followup_date></followup_date> <!-- generated by form or empty (in days) -->
            <outcome></outcome> <!-- how the case was closed -->
        </case>
    """
    case_block = xformdoc.xpath(const.CASE_TAG)
    if case_block:
        # {u'case_type': u'diarrhea', u'followup_type': u'followup-chw', u'followup_date': u'7', 
        #  u'patient_id': u'5a105a68b050d0149eb1d23fa75d3175'}
        # create case
        # hack up pregnancy, since we treat it differently than everything
        # else
        if xformdoc.namespace == HEALTHY_PREGNANCY_NAMESPACE:
            return get_healthy_pregnancy_case(case_block, xformdoc, encounter)
    
        followup_type = case_block[const.FOLLOWUP_TYPE_TAG] \
                            if const.FOLLOWUP_TYPE_TAG in case_block else None
        if not followup_type or followup_type == const.FOLLOWUP_TYPE_NONE:
            return _new_unentered_case(case_block, encounter)
        if const.FOLLOWUP_TYPE_REFER == followup_type:
            return _new_referral(case_block, encounter)
        if const.FOLLOWUP_TYPE_FOLLOW_CHW == followup_type:
            return _new_chw_follow(case_block, encounter)
        if const.FOLLOWUP_TYPE_FOLLOW_CLINIC == followup_type:
            return _new_clinic_follow(case_block, encounter)
        if const.FOLLOWUP_TYPE_CLOSE == followup_type:
            return _new_closed_case(case_block, encounter)
        # TODO: be more graceful
        log_exception(CaseLogicException("Unknown followup type: %s in doc %s" % (followup_type, xformdoc.get_id)))
        return None
    
    return None

def get_healthy_pregnancy_case(case_block, xformdoc, encounter):
    # Any pregnancy case that is created that hasn't been closed by a delivery 
    # gets a followup.  The followups become active at week 40 and expires in
    # week 44 of the pregnancy
    # The CHW should track the delivery and give an outcome to the pregnancy.
    
    # This is currently hacked up to only be generated by first visits until
    # we have some more reasonable pregnancy linkages.
    if not xformdoc.xpath("first_visit"):
        return None
    else:
        def get_lmp(doc):
            if (doc.xpath("first_visit/lmp")):
                return string_to_datetime(doc.xpath("first_visit/lmp"))
            elif (doc.xpath("gestational_age")):
                return string_to_datetime(doc.encounter_date) + timedelta(days=7*int(doc.xpath("gestational_age")))
        
        lmp = get_lmp(xformdoc)
        if lmp:
            send_to_phone = True
            reason = "pregnancy_expecting_outcome"
        else:
            send_to_phone = False
            reason = "unknown_lmp"
        
        bhoma_case = PatientCase(_id=get_bhoma_case_id_from_form(xformdoc), 
                                 opened_on=datetime.combine(encounter.visit_date, time()),
                                 modified_on=datetime.utcnow(),
                                 type=const.CASE_TYPE_PREGNANCY,
                                 encounter_id=encounter.get_id,
                                 patient_id=case_block[const.PATIENT_ID_TAG],
                                 outcome="",
                                 send_to_phone=send_to_phone,
                                 send_to_phone_reason=reason)
        cccase = _get_first_commcare_case(encounter, bhoma_case=bhoma_case, 
                                          case_id=get_commcare_case_id_from_block(encounter, bhoma_case, case_block))
        bhoma_case.status = "pending outcome"
        cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_PREGNANCY
        
        if lmp:
            # starts and becomes active the same day, 40 weeks from LMP
            bhoma_case.lmp = lmp
            cccase.start_date = (lmp + timedelta(days= 7 * 40)).date()
            cccase.missed_appointment_date = cccase.start_date
            cccase.activation_date = cccase.start_date
            cccase.due_date = cccase.activation_date + timedelta(days=DAYS_AFTER_PREGNANCY_ACTIVE_DUE)
        bhoma_case.commcare_cases = [cccase]
        return bhoma_case
        
    return None

def _get_bhoma_case(case_block, encounter):
    """
    Shared case attributes.  
    """
    send_followup, send_followup_reason = should_send_followup_to_phone(encounter)
    return PatientCase(_id=get_bhoma_case_id_from_form(encounter.get_xform()), 
                       opened_on=datetime.combine(encounter.visit_date, time()),
                       modified_on=datetime.utcnow(),
                       type=case_block[const.CASE_TAG_TYPE],
                       encounter_id=encounter.get_id,
                       patient_id=case_block[const.PATIENT_ID_TAG],
                       outcome=case_block[const.OUTCOME_TAG],
                       send_to_phone=send_followup,
                       send_to_phone_reason=send_followup_reason
                       )
    
def _get_first_commcare_case(encounter, bhoma_case, case_id):
    
    name = get_commcare_case_name(encounter, bhoma_case)
    user_id = get_user_id(encounter)
    
    cccase = new_commcare_case(case_id=case_id,
                               name=name,
                               type=bhoma_case.type,
                               opened_on=bhoma_case.opened_on, 
                               bhoma_case_id=bhoma_case._id, 
                               user_id=user_id,
                               modified_on=bhoma_case.modified_on, 
                               encounter_id=bhoma_case.encounter_id)
    return cccase


def _followup_type_from_block(case_block):
    return follow_type_from_form(case_block[const.FOLLOWUP_TYPE_TAG])

def _new_referral(case_block, encounter):
    case = _get_bhoma_case(case_block, encounter)
    cccase = _get_first_commcare_case(encounter, bhoma_case=case, 
                                      case_id=get_commcare_case_id_from_block(encounter, case, case_block))
    case.status = "referred"
    cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_HOSPITAL
    
    cccase.activation_date = (case.opened_on + timedelta(days=DAYS_AFTER_REFERRAL_CHECK - DAYS_BEFORE_FOLLOW_ACTIVE)).date()
    cccase.start_date = cccase.activation_date - timedelta(days=DAYS_BEFORE_ACTIVE_START)
    cccase.due_date = cccase.activation_date + timedelta(DAYS_AFTER_ACTIVE_DUE)
    case.commcare_cases = [cccase]
    return case

def _new_chw_follow(case_block, encounter):
    case = _get_bhoma_case(case_block, encounter)
    cccase = _get_first_commcare_case(encounter, bhoma_case=case, 
                                      case_id=get_commcare_case_id_from_block(encounter, case, case_block))
    case.commcare_cases = [cccase]
    case.status = "followup with chw"
    cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_CHW
    case.commcare_cases = [cccase]
    try:
        follow_days = int(case_block[const.FOLLOWUP_DATE_TAG])
    except ValueError:
        # we didn't have a valid integer, rather than guess at 
        # the date of follow up we should either default to 
        # something standard or ignore.  for now we ignore
        return case
    cccase.activation_date = (case.opened_on + timedelta(days=follow_days - DAYS_BEFORE_FOLLOW_ACTIVE)).date()
    cccase.start_date = cccase.activation_date - timedelta(days=DAYS_BEFORE_ACTIVE_START)
    cccase.due_date = cccase.activation_date + timedelta(DAYS_AFTER_ACTIVE_DUE)
    return case

def _new_clinic_follow(case_block, encounter):  
    case = _get_bhoma_case(case_block, encounter)
    cccase = _get_first_commcare_case(encounter, bhoma_case=case, 
                                      case_id=get_commcare_case_id_from_block(encounter, case, case_block))
    case.commcare_cases = [cccase]
    cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_MISSED_APPT
    case.status = const.STATUS_RETURN_TO_CLINIC
    try:
        follow_days = int(case_block[const.FOLLOWUP_DATE_TAG])
    except ValueError:
        return case
    
    appt_date = (cccase.opened_on + timedelta(follow_days)).date()
    add_missed_appt_dates(cccase, appt_date)
    return case

def _new_unentered_case(case_block, encounter):
    """
    Case from 'none' selected or no outcome chosen.
    """
    # we treat these as generating a case that follows same rules as others
    case = _get_bhoma_case(case_block, encounter)
    cccase = _get_first_commcare_case(encounter, bhoma_case=case, 
                                      case_id=get_commcare_case_id_from_block(encounter, case, case_block))
    
    case.status = "followup with chw"
    cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_CHW
    
    cccase.activation_date = (case.opened_on + timedelta(days=DAYS_AFTER_UNDATED_FOLLOWUP_ACTIVE)).date()
    cccase.start_date = cccase.activation_date - timedelta(days=DAYS_BEFORE_ACTIVE_START)
    cccase.due_date = cccase.activation_date + timedelta(days=DAYS_AFTER_ACTIVE_DUE)
    case.commcare_cases = [cccase]
    return case

def _new_closed_case(case_block, encounter):
    """
    Case from closing block
    """
    case = _get_bhoma_case(case_block, encounter)
    case.status = "closed at clinic"
    cccase = _get_first_commcare_case(encounter, bhoma_case=case, 
                                      case_id=get_commcare_case_id_from_block(encounter, case, case_block))
    close_action = CommCareCaseAction(action_type=const.CASE_ACTION_CLOSE, date=case.opened_on, 
                                      closed_on=case.opened_on, outcome=case.outcome)
    cccase.actions.append(close_action)
    cccase.closed = True
    case.commcare_cases = [cccase]
    case.closed = True
    case.closed_on = case.opened_on
    return case