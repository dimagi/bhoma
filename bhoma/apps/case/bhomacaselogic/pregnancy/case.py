from datetime import datetime, time, timedelta
from bhoma.apps.case.bhomacaselogic.shared import get_bhoma_case_id_from_pregnancy,\
    get_patient_id_from_form, get_commcare_case_id_from_block
from bhoma.apps.case.models.couch import PatientCase
from bhoma.apps.case import const
from bhoma.apps.case.util import get_first_commcare_case
from bhoma.apps.case.bhomacaselogic.shared import DAYS_AFTER_PREGNANCY_ACTIVE_DUE
import logging



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
            # create the case from this encounter
            patient.cases.append(get_healthy_pregnancy_case(found_preg, encounter))
        else:
            # todo check updates/close
            logging.error("check updates here!")
            pass
    
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
                             outcome="",
                             send_to_phone=send_to_phone,
                             send_to_phone_reason=reason)
    cccase = get_first_commcare_case(encounter, bhoma_case=bhoma_case, 
                                     case_id=get_commcare_case_id_from_block(encounter,bhoma_case))
    bhoma_case.status = "pending outcome"
    cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_PREGNANCY
    
    if lmp:
        # starts and becomes active the same day, 42 weeks from LMP
        bhoma_case.lmp = lmp
        cccase.start_date = lmp + timedelta(days= 7 * 42)
        cccase.missed_appointment_date = cccase.start_date
        cccase.activation_date = cccase.start_date
        cccase.due_date = cccase.activation_date + timedelta(days=DAYS_AFTER_PREGNANCY_ACTIVE_DUE)
    bhoma_case.commcare_cases = [cccase]
    return bhoma_case
