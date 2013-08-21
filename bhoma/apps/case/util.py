"""
Bhoma-specific utility methods for cases.  
"""

from datetime import datetime, time, timedelta
from bhoma.apps.case import const
from bhoma.apps.case.models import CommCareCase
from dimagi.utils import parsing
from bhoma.apps.case.models import CommCareCaseAction
from bhoma.apps.patient.models import CPatient
from dimagi.utils.couch import uid
from bhoma.apps.case.models.couch import PatientCase
from dimagi.utils.parsing import string_to_datetime
from bhoma.apps.case.bhomacaselogic.shared import *
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS,\
    HEALTHY_PREGNANCY_NAMESPACE, CLASSIFICATION_CLINIC
from bhoma.apps.case.exceptions import CaseLogicException
from dimagi.utils.dates import safe_date_add 
from bhoma.apps.case.bhomacaselogic.followups import get_followup_type,\
    FollowupRandom
from bhoma.apps.case.bhomacaselogic.ltfu import close_as_lost
from bhoma.apps.case.bhomacaselogic.random import predictable_random

def close_previous_cases_from_new_form(patient, form, encounter):
    """
    From the patient, find any open cases and if necessary, close them.
    
    Rules for closing a case:
     1. A clinic visit for outside of the LTFU window of a previous 
        case closes that case with outcome "ltfu" 
     2. A clinic visit form within the LTFU window of a previous case 
        closes that case with outcome "returned to clinic" UNLESS 
        it's a pregnancy case, in which case it's not touched.
     3. The current case is not touched by this method even if it falls
        in the LTFU range from the current time.
     
    Assumptions:
     1. The form is the latest form in the patient (no previous forms
        will get added, and if they do it will result in a full rebuild)
     2. All previous forms have already been correctly processed
    """
    for case in patient.cases:
        if not case.closed and case.opened_on.date() < encounter.visit_date:
            # NOTE: do we close pregnancy LTFU here or elsewhere? 
            # Here seems fine for now, since lost is lost, even on pregnancy
            if case.ltfu_date and case.ltfu_date < encounter.visit_date \
            and case.ltfu_date < datetime.utcnow().date():
                close_as_lost(case)
            else:
                # coming back to the clinic closes any open cases before the date of 
                # that visit, since you are allowed _at most_ one open case at a time.
                # however, pregnancy cases get closed by a separate workflow.  
                # see bhoma/apps/case/pregnancy/case.py
                encounter_info = ENCOUNTERS_BY_XMLNS.get(form.namespace)
                if encounter_info.classification == CLASSIFICATION_CLINIC \
                and case.type != const.CASE_TYPE_PREGNANCY:
                    case.manual_close(const.Outcome.RETURNED_TO_CLINIC, datetime.combine(encounter.visit_date, time()))
    patient.save()
                    
                    
def apply_case_updates(case, followup_type, encounter):
    """
    Given a case and followup type, apply the appropriate actions to the case.
    """
    # this randomly chosen business is to send some percent 
    # of followups to phones, even if the normal logic wouldn't
    # have sent them. The rest of this method is needlessly complicated
    # by this requirement
    randomly_chosen = predictable_random(encounter.get_xform().sha1,
                                         const.AUTO_FU_PROBABILITY)
    if followup_type.closes_case() and not randomly_chosen:
        # if it closes the case, just mark it as such and attach an outcome
        case.outcome = followup_type.get_outcome()
        case.closed = True
        case.closed_on = case.opened_on
    else:
        # have to add this check, since the follow up types that 
        # close the case don't support these two fields.
        if not followup_type.closes_case():
            case.status = followup_type.get_status()
            case.ltfu_date = followup_type.get_ltfu_date(case.opened_on)
        if case.send_to_phone:
            # create a commcare case for this to go to the phone
            # this is the normal workflow
            _commcare_case_create_workflow(case, followup_type, encounter)
        elif randomly_chosen:
            # create a commcare case for this to go to the phone
            # this is the randomly chosen workflow
            # note that this will actually potentially create cases
            # for dead patients, but they will be automatically closed
            # by the signal that deals with death, so this is ok
            random_followup_type = FollowupRandom()
            # mark it as going to the phone
            case.send_to_phone = True
            case.send_to_phone_reason = const.SendToPhoneReasons.RANDOMLY_CHOSEN
            # override the status and ltfu date for all random follow ups
            case.status = random_followup_type.get_status()
            case.ltfu_date = random_followup_type.get_ltfu_date(case.opened_on)
            case.random_fu_probability = const.AUTO_FU_PROBABILITY
            _commcare_case_create_workflow(case, random_followup_type, encounter)    
            
def _commcare_case_create_workflow(case, followup_type, encounter):
    cccase = get_first_commcare_case(encounter,
                                     bhoma_case=case,
                                     case_id=get_commcare_case_id_from_block(
                                         encounter, case, encounter.get_xform().xpath(const.CASE_TAG)
                                     ))
    cccase.followup_type = followup_type.get_phone_followup_type()
    cccase.activation_date = followup_type.get_activation_date(case.opened_on)
    cccase.start_date = followup_type.get_start_date(case.opened_on)
    cccase.due_date = followup_type.get_due_date(case.opened_on)
    cccase.missed_appointment_date = followup_type.get_missed_appointment_date(case.opened_on)
    case.commcare_cases = [cccase]            
            
            
def get_or_update_bhoma_case(xformdoc, encounter):
    """
    Process Bhoma XML - which looks like this:
        <case>
            <patient_id></patient_id> <!-- patient -->
            <case_type></case_type> <!-- diagnosis -->
            <followup_type></followup_type> <!-- referral, facility followup, closed -->
            <followup_date></followup_date> <!-- generated by form or empty (in days) -->
        </case>
    """
    if xformdoc.namespace == HEALTHY_PREGNANCY_NAMESPACE:
        # HACK: pregnancy cases must be dealt with after-the-fact so do nothing here
        return None
    
    followup_type = get_followup_type(xformdoc)
    if followup_type.opens_case():
        case = _get_bhoma_case(xformdoc.xpath(const.CASE_TAG), encounter)
        apply_case_updates(case, followup_type, encounter)
        return case
    else:
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
                       send_to_phone=send_followup,
                       send_to_phone_reason=send_followup_reason
                       )
    
def get_first_commcare_case(encounter, bhoma_case, case_id):
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


