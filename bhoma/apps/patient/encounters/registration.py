import os
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.patient.models import CPatient, CRelationship
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
    
def relationship_from_instance(doc):
    return CRelationship(
        type='mother',
        patient_id=doc.get('mother_id'),
        no_id_reason=doc.get('mother_no_id_reason'),
        no_id_first_name=doc.get('mother_fname'),
        no_id_last_name=doc.get('mother_lname'),
        no_id_birthdate=string_to_datetime(doc.get('mother_dob')).date() if doc.get('mother_dob') else None,
    )

