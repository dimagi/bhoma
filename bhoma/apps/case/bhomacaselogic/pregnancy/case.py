from datetime import datetime, time, timedelta
from bhoma.apps.case.bhomacaselogic.shared import get_bhoma_case_id_from_pregnancy,\
    get_patient_id_from_form, get_commcare_case_id_from_block
from bhoma.apps.case.models.couch import PatientCase
from bhoma.apps.case import const
from bhoma.apps.case.util import get_first_commcare_case
from bhoma.apps.case.bhomacaselogic.shared import DAYS_AFTER_PREGNANCY_ACTIVE_DUE
from bhoma.apps.case.const import CASE_TYPE_PREGNANCY


def update_pregnancy_cases(patient, encounter):
    # assumes the pregnancies have already been updated
    # just sees if this encounter belongs in any of them
    found_preg = None
    for preg in patient.pregnancies:
        if encounter.xform_id in preg.form_ids:
            found_preg = preg
            break
    if found_preg:
        if found_preg.anchor_form_id == encounter.xform_id:
            # the anchor creates the case from this encounter
            patient.cases.append(get_healthy_pregnancy_case(found_preg, encounter))
        else:
            # check if there's a pregnancy case associated with this
            # and make sure it gets updated if so
            preg_case = get_matching_pregnancy_case(patient, found_preg)
            if preg_case:
                preg_case.outcome = found_preg.outcome
                preg_case.closed = found_preg.closed
                preg_case.closed_on = found_preg.closed_on
            
def get_healthy_pregnancy_case(pregnancy, encounter):
    # Any pregnancy case that is created that hasn't been closed by a delivery 
    # gets a followup.  The followups become active at week 42 and expires in
    # week 46 of the pregnancy
    # The CHW should track the delivery and give an outcome to the pregnancy.
    
    lmp = pregnancy.lmp
    # TODO: is this check/logic necessary?
    if lmp:
        send_to_phone = True
        reason = "pregnancy_expecting_outcome"
    else:
        send_to_phone = False
        reason = "unknown_lmp"
    
    #send_to_phone = True
    #reason = "pregnancy_expecting_outcome"
    bhoma_case = PatientCase(_id=get_bhoma_case_id_from_pregnancy(pregnancy), 
                             opened_on=datetime.combine(encounter.visit_date, time()),
                             modified_on=datetime.utcnow(),
                             type=const.CASE_TYPE_PREGNANCY,
                             encounter_id=encounter.get_id,
                             patient_id=get_patient_id_from_form(encounter.get_xform()),
                             # patient_id=case_block[const.PATIENT_ID_TAG], merge conflict?
                             outcome = pregnancy.outcome,
                             closed = pregnancy.closed,
                             closed_on = pregnancy.closed_on,
                             send_to_phone=send_to_phone,
                             send_to_phone_reason=reason)
    bhoma_case.status = "pending outcome"
    
    if send_to_phone and not bhoma_case.closed:
        cccase = get_first_commcare_case(encounter, bhoma_case=bhoma_case, 
                                     case_id=get_commcare_case_id_from_block(encounter,bhoma_case))
        cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_PREGNANCY
    
        # starts and becomes active the same day, 42 weeks from LMP
        bhoma_case.lmp = lmp
        cccase.start_date = lmp + timedelta(days= 7 * 42)
        cccase.missed_appointment_date = cccase.start_date
        cccase.activation_date = cccase.start_date
        cccase.due_date = cccase.activation_date + timedelta(days=DAYS_AFTER_PREGNANCY_ACTIVE_DUE)
        bhoma_case.commcare_cases = [cccase]
    return bhoma_case

def get_matching_pregnancy_case(patient, pregnancy):
    if pregnancy.is_anchored():
        # if it's anchored there should be a case for it
        for case in patient.cases:
            if case.type == CASE_TYPE_PREGNANCY and \
               case.get_encounter().xform_id == pregnancy.anchor_form_id:
                return case
        
                
            