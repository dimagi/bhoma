import os
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.patient.models import CPatient
from dimagi.utils.parsing import string_to_boolean, string_to_datetime
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.xforms.util import get_xform_by_namespace
from datetime import datetime

def patient_from_instance(doc):
    """
    From a registration document object, create a Patient.
    """
    # TODO: clean up / un hard-code
    patient = CPatient(first_name=doc["first_name"],
                       last_name=doc["last_name"],
                       birthdate=string_to_datetime(doc["birthdate"]).date() if doc["birthdate"] else None,
                       birthdate_estimated=string_to_boolean(doc["birthdate_estimated"]),
                       gender=doc["gender"],
                       patient_id=doc["patient_id"],
                       created_on=datetime.utcnow())
    return patient
    