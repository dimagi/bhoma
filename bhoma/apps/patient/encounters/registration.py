import os
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.patient.models import CPatient, CRelationship
from dimagi.utils.parsing import string_to_boolean, string_to_datetime
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.xforms.util import get_xform_by_namespace
from datetime import datetime
from dimagi.utils.couch.database import get_db
from datetime import date, timedelta

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
    
def mother_birthdate_range(baby_birthdate):
    return (
        (baby_birthdate if baby_birthdate else date.today() - timedelta(days=5*365.2425)) - timedelta(days=55*365.2425),
        (baby_birthdate if baby_birthdate else date.today()) - timedelta(days=10*365.2425)
    )

def extract_birthdate(doc):
    birthdate = doc.get('birthdate')
    if not birthdate:
        birthdate = doc.get('dob')
    return string_to_datetime(birthdate).date() if birthdate else None

def relationship_from_instance(doc):
    db = get_db()

    mother_pat_id = doc.get('mother_id')
    if mother_pat_id:
        if mother_pat_id == doc.get('id'):
            #they entered the baby's ID as the mother's ID
            return

        #look up that ID exists, that patient data (sex/age) makes sense, and only one candidate match
        matches = list(db.view('patient/by_bhoma_id', startkey="%s" % mother_pat_id, endkey="%szzzz" % mother_pat_id, reduce=False, include_docs=True))
        def valid_mother(d):
            min_mother_bd, max_mother_bd = mother_birthdate_range(extract_birthdate(doc))
            mother_bd = extract_birthdate(d)
            return d.get('gender') == 'f' and (mother_bd >= min_mother_bd and mother_bd <= max_mother_bd)
        mothers = filter(lambda r: valid_mother(r['doc']), matches)
        return CRelationship(type='mother', patient_id=mother_pat_id, patient_uuid=mothers[0]['doc']['_id'] if len(mothers) == 1 else None)
    else:


        return CRelationship(
            type='mother',
            patient_id=doc.get('mother_id'),
            no_id_reason=doc.get('mother_no_id_reason'),
            no_id_first_name=doc.get('mother_fname'),
            no_id_last_name=doc.get('mother_lname'),
            no_id_birthdate=string_to_datetime(doc.get('mother_dob')).date() if doc.get('mother_dob') else None,
            )

