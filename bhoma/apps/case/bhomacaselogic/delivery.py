from bhoma.apps.case import const
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_delivery_encounter
from bhoma.apps.case.models.couch import Delivery, PatientCase
from dimagi.utils.dates import force_to_date
from datetime import datetime, time, timedelta
from bhoma.apps.case.util import get_first_commcare_case


def is_new_delivery(encounter):
    return encounter.get_xform().xpath('newborn_eval/vital_status') == 'alive'

def get_delivery_date(encounter):
    datestring = encounter.get_xform().xpath('delivery/date')
    if datestring:
        return force_to_date(datestring)

def get_bhoma_case_id_from_delivery(delivery):
    """
    Generate a unique (but deterministic) bhoma case id from pregnancy data.
    """
    return "delivery-%s" % delivery.xform_id

def get_commcare_case_id_from_delivery(delivery, visit_number):
    return "delivery-fu-{number}-{id}".format(
        number=visit_number, id=delivery.xform_id
    )

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
        # we'll generate two commcare cases immedieately
        ccfu1 = get_first_commcare_case(
            encounter,
            bhoma_case=bhoma_case,
            case_id=get_commcare_case_id_from_delivery(delivery, 1)
        )
        ccfu1.followup_type = const.PHONE_FOLLOWUP_TYPE_DELIVERY

        # starts after 4 days, active after 6 days
        ccfu1.start_date = delivery.date + timedelta(days=4)
        ccfu1.missed_appointment_date = None # TODO: do we need to change this so the phone can use it?
        ccfu1.activation_date = delivery.date + timedelta(days=6)
        ccfu1.due_date = ccfu1.activation_date + timedelta(days=10)
        ccfu1.ltfu_date = ccfu1.activation_date + timedelta(days=20)

        ccfu2 = get_first_commcare_case(
            encounter,
            bhoma_case=bhoma_case,
            case_id=get_commcare_case_id_from_delivery(delivery, 2)
        )
        ccfu2.followup_type = const.PHONE_FOLLOWUP_TYPE_DELIVERY

        # starts after 23 days, active after 28 days, due in 5, ltfu after 42
        ccfu2.start_date = delivery.date + timedelta(days=23)
        ccfu2.missed_appointment_date = None # TODO: do we need to change this so the phone can use it?
        ccfu2.activation_date = delivery.date + timedelta(days=28)
        ccfu2.due_date = ccfu2.activation_date + timedelta(days=5)
        ccfu2.ltfu_date = ccfu2.activation_date + timedelta(days=42)


        bhoma_case.commcare_cases = [ccfu1, ccfu2]
    return bhoma_case

