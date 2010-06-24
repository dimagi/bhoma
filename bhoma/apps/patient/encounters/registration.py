import os
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.patient.models import CPatient
from bhoma.utils.parsing import string_to_boolean, string_to_date
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.xforms.util import get_xform_by_namespace

NAMESPACE = "http://openrosa.org/bhoma/registration"
NAME      = "registration"

    # CZUE: abandoning callbacks for now so commenting this out...
    # delete and recreate the callbacks automaticall 
    # should we do this only on some other condition?  
    # XFormCallback.objects.filter(xform=RegistrationEncounter.xform).delete()
    # XFormCallback.objects.create(xform=RegistrationEncounter.xform, 
    #                              callback="bhoma.apps.patient.encounters.registration.form_complete")

def patient_from_instance(doc):
    """
    From a registration xform document object, create a Patient.
    """
    # TODO: clean up / un hard-code
    patient = CPatient(first_name=doc["first_name"],
                       last_name=doc["last_name"],
                       birthdate=string_to_date(doc["birthdate"]).date(),
                       birthdate_estimated=string_to_boolean(doc["birthdate_estimated"]),
                       gender=doc["gender"])
    patient.encounters.append(Encounter.from_xform(doc, NAME))
    return patient
    