from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_delivery_encounter
from bhoma.apps.case.models.couch import Delivery
from dimagi.utils.dates import force_to_date

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
            delivery_date=get_delivery_date(encounter),
        )
        patient.deliveries.append(new_delivery)

    # todo: cases
    return patient


