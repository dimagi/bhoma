"""
Bhoma-specific utility methods for cases.  TODO: abstract / move this somewhere more
appropriate. 
"""

from datetime import datetime, time, timedelta
from bhoma.apps.case import const
from bhoma.apps.case.models import CommCareCase
from bhoma.utils import parsing
from bhoma.apps.case.models import CommCareCaseAction, CReferral
from bhoma.apps.patient.models import CPatient
from couchdbkit.schema.properties_proxy import SchemaProperty
from bhoma.utils.couch import uid
from bhoma.apps.case.models.couch import PatientCase
from bhoma.utils.parsing import string_to_datetime

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
    case_block = xformdoc[const.CASE_TAG] if const.CASE_TAG in xformdoc else None
    if case_block:
        # {u'case_type': u'diarrhea', u'followup_type': u'followup-chw', u'followup_date': u'7', 
        #  u'patient_id': u'5a105a68b050d0149eb1d23fa75d3175'}
        # create case
        followup_type = case_block[const.FOLLOWUP_TYPE_TAG]
        if const.FOLLOWUP_TYPE_REFER == followup_type:
            return _new_referral(case_block, xformdoc, encounter)
        if const.FOLLOWUP_TYPE_FOLLOW_CHW == followup_type:
            return _new_chw_follow(case_block, xformdoc, encounter)
        if const.FOLLOWUP_TYPE_FOLLOW_CLINIC == followup_type:
            return _new_clinic_follow(case_block, xformdoc, encounter)
        if const.FOLLOWUP_TYPE_CLOSE == followup_type:
            return _new_closed_case(case_block, xformdoc, encounter)
        # TODO: be more graceful
        raise Exception("Unknown followup type: %s" % followup_type)
    return None

def _set_common_attrs(case_block, xformdoc, encounter):
    """
    Shared case attributes.  
    """
    
    _id = uid.new()
    opened_on = datetime.combine(encounter.visit_date, time())
    type = case_block[const.CASE_TAG_TYPE]
    outcome = case_block[const.OUTCOME_TAG]
    
    patient_id = case_block[const.PATIENT_ID_TAG]
    encounter_id = encounter.get_id
    modified_on = datetime.utcnow()
    
    case = PatientCase(_id=_id, opened_on=opened_on, modified_on=modified_on, 
                       type=type, encounter_id=encounter_id, patient_id=patient_id,
                       outcome=outcome)
    
    
    # also make and add the CommCareCase
    # these are somewhat arbitraty
    name = "%s|%s" % (encounter.type, type)
    # the external id is the bhoma case id.  also redundant since this is a child of that
    external_id = _id
    if encounter.metadata:
        user_id = encounter.metadata.user_id
    else:
        user_id = None
        
    # create action
    create_action = CommCareCaseAction(type=const.CASE_ACTION_CREATE, opened_on=opened_on)
    case_id = uid.new()
    cccase = CommCareCase(case_id=case_id, opened_on=opened_on, modified_on=modified_on, 
                 type=type, name=name, user_id=user_id, external_id=external_id, 
                 encounter_id=encounter_id, actions=[create_action,])
    case.commcare_cases.append(cccase)
    return case

def _new_referral(case_block, xformdoc, encounter):
    case = _set_common_attrs(case_block, xformdoc, encounter)
    # TODO: add the referral 
    return case

def _new_chw_follow(case_block, xformdoc, encounter):
    case = _set_common_attrs(case_block, xformdoc, encounter)
    cccase = case.commcare_cases[0]
    cccase.followup_type = case_block[const.FOLLOWUP_TYPE_TAG]
    follow_days = int(case_block[const.FOLLOWUP_DATE_TAG])
    cccase.due_date = (case.opened_on + timedelta(days=follow_days)).date()
    return case

def _new_clinic_follow(case_block, xformdoc, encounter):
    case = _set_common_attrs(case_block, xformdoc, encounter)
    cccase = case.commcare_cases[0]
    cccase.followup_type = case_block[const.FOLLOWUP_TYPE_TAG]
    follow_days = int(case_block[const.FOLLOWUP_DATE_TAG])
    cccase.due_date = (case.opened_on + timedelta(days=follow_days)).date()
    return case

def _new_closed_case(case_block, xformdoc, encounter):
    """
    Case from closing block
    """
    case = _set_common_attrs(case_block, xformdoc, encounter)
    close_action = CommCareCaseAction(type=const.CASE_ACTION_CLOSE, closed_on=case.opened_on, outcome=case.outcome)
    case.commcare_cases[0].actions.append(close_action)
    case.commcare_cases[0].closed = True
    case.closed = True
    return case

