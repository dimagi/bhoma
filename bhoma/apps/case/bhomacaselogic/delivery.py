from bhoma.apps.case import const
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_delivery_encounter
from bhoma.apps.case.bhomacaselogic.shared import get_bhoma_case_id_from_delivery, get_patient_id_from_form
from bhoma.apps.case.models.couch import Delivery, PatientCase
from dimagi.utils.dates import force_to_date
from datetime import datetime, time, timedelta


def is_new_delivery(encounter):
    return encounter.get_xform().xpath('newborn_eval/vital_status') == 'alive'

def get_delivery_date(encounter):
    datestring = encounter.get_xform().xpath('delivery/date')
    if datestring:
        return force_to_date(datestring)

def update_deliveries(patient, encounter):
    """
    From a patient object, update the list of deliveries.
    """
    assert is_delivery_encounter(encounter)
    # create a delivery if it is a new one.
    if is_new_delivery(encounter):
        new_delivery = Delivery(
            xform_id=encounter.get_xform()._id,
            date=get_delivery_date(encounter),
        )
        patient.deliveries.append(new_delivery)
        patient.cases.append(get_delivery_case(patient, encounter, new_delivery))

    return patient

def get_delivery_case(patient, encounter, delivery):
    # All deliveries get two follow ups.

    if delivery.date:
        send_to_phone = True
        reason = "delivery_needing_followup"
    else:
        send_to_phone = False
        reason = "unknown_delivery_date"

    # todo proper ltfu date
    ltfu_date = delivery.date + timedelta(days=7*42)
    bhoma_case = PatientCase(
        _id=get_bhoma_case_id_from_delivery(delivery),
        opened_on=datetime.combine(encounter.visit_date, time()),
        modified_on=datetime.utcnow(),
        type=const.CASE_TYPE_DELIVERY,
        encounter_id=encounter.get_id,
        patient_id=patient._id,
        ltfu_date=ltfu_date,
        status="pending outcome",
        outcome=delivery.outcome,
        closed=delivery.closed,
        closed_on=delivery.closed_on,
        send_to_phone=send_to_phone,
        send_to_phone_reason=reason,
    )

    if send_to_phone and not bhoma_case.closed:
        pass
        # todo ccase
        # cccase = get_first_commcare_case(encounter, bhoma_case=bhoma_case,
        #                              case_id=get_commcare_case_id_from_block(encounter,bhoma_case))
        # cccase.followup_type = const.PHONE_FOLLOWUP_TYPE_PREGNANCY
        #
        # # starts and becomes active the same day, 42 weeks from LMP
        # bhoma_case.lmp = lmp
        # cccase.start_date = lmp + timedelta(days= 7 * 42)
        # cccase.missed_appointment_date = cccase.start_date
        # cccase.activation_date = cccase.start_date
        # cccase.due_date = cccase.activation_date + timedelta(days=DAYS_AFTER_PREGNANCY_ACTIVE_DUE)
        # bhoma_case.commcare_cases = [cccase]
    return bhoma_case

