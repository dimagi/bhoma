from bhoma.apps.patient.encounters import config
from bhoma.apps.case.util import get_first_commcare_case, apply_case_updates
from bhoma.apps.case.models.couch import PatientCase
from bhoma.apps.case.bhomacaselogic.shared import get_bhoma_case_id_from_form,\
    get_commcare_case_id_from_block
from datetime import datetime, time
from bhoma.apps.case.bhomacaselogic.followups import FollowupChwReferral,\
    FollowupType
from bhoma.apps.case import const

def process_referral(patient, encounter):
    form = encounter.get_xform()
    assert form.namespace == config.CHW_REFERRAL_NAMESPACE
    # by this time we've already gone through the trouble to find
    # the patient so create the case for the referral.
    
    if form.xpath("life_threatening") == "y":
        # it's life threatening! send it to the phone
        send_to_phone = True
        send_to_phone_reason = "life_threatening_referral"
    else:
        send_to_phone = False
        send_to_phone_reason = ""
    case = PatientCase(_id=get_bhoma_case_id_from_form(form), 
                       opened_on=datetime.combine(encounter.visit_date, time()),
                       modified_on=datetime.utcnow(),
                       type=form.xpath("complaint"),
                       encounter_id=encounter.get_id,
                       patient_id=patient.get_id,
                       send_to_phone=send_to_phone,
                       send_to_phone_reason=send_to_phone_reason)
                   
    followup_type = FollowupChwReferral(FollowupType.FACILITY, [const.FOLLOWUP_TYPE_CHW_REFERRAL])
    apply_case_updates(case, followup_type, encounter)
    patient.update_cases([case,])