import os
from bhoma.apps.encounter.models import EncounterType
from bhoma.apps.patient.models import CPatient, CRelationship
from dimagi.utils.parsing import string_to_boolean, string_to_datetime
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.xforms.util import get_xform_by_namespace
from datetime import datetime
from dimagi.utils.couch.database import get_db
from datetime import date, timedelta
from touchforms.formplayer.autocomplete import damerau_levenshtein_dist

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

def extract_birthdate(doc, field=None):
    if field:
        birthdate = doc.get(field)
    else:
        birthdate = doc.get('birthdate')
        if not birthdate:
            birthdate = doc.get('dob')
    return string_to_datetime(birthdate).date() if birthdate else None

def relationship_from_instance(doc):
    MOTHER_AGE_MATCH_FUZZINESS = timedelta(days=365.2425)

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
            return d.get('gender') == 'f' and (mother_bd and mother_bd >= min_mother_bd and mother_bd <= max_mother_bd)
        mothers = filter(lambda r: valid_mother(r['doc']), matches)
        if len(mothers) == 1:
            mother = mothers[0]['doc']
            return CRelationship(
                type='mother',
                patient_id=mother_pat_id,
                patient_uuid=mother['_id'],
                no_id_first_name=mother['first_name'],
                no_id_last_name=mother['last_name'],
            )
        else:
            return CRelationship(type='mother', patient_id=mother_pat_id)
    else:
        #do fuzzy search
        mother_fname = doc.get('mother_fname')
        mother_lname = doc.get('mother_lname')
        mother_dob = extract_birthdate(doc, 'mother_dob')
        mother_uuid = None

        if all([mother_fname, mother_lname, mother_dob]):
            mother = None

            #get exact name match, women, birthdate within specified tolerance
            matches = list(db.view('patient/by_name', startkey=[mother_lname, mother_fname], endkey=[mother_lname, mother_fname, {}], reduce=False, include_docs=True))
            def candidate_mother(d):
                cand_dob = extract_birthdate(d)
                age_diff = abs(mother_dob - cand_dob) if cand_dob else None
                return d.get('gender') == 'f' and (age_diff is not None and age_diff <= MOTHER_AGE_MATCH_FUZZINESS)
            matches = filter(lambda r: candidate_mother(r['doc']), matches)

            if len(matches) == 1:
                mother = matches[0]
            elif len(matches) > 1:
                #ambiguous; filter further by village
                mother_village = doc.get('village') #assume same as baby's village
                def match_village(v):
                    if mother_village and v:
                        metric = damerau_levenshtein_dist(mother_village, v)
                        metric_max = len(mother_village) / 4 #len 1-3: exact match, len 4-7: dist 1, len 8-11: dist 2, etc.
                        return metric <= metric_max
                    else:
                        return False
                matches = filter(lambda r: match_village(r['doc']['address']['village']), matches)
                if len(matches) == 1:
                    mother = matches[0]

            if mother:
                mother_uuid = mother['doc']['_id']
                mother_pat_id = mother['doc']['patient_id']

        return CRelationship(
            type='mother',
            patient_uuid=mother_uuid,
            patient_id=mother_pat_id,
            no_id_reason=doc.get('mother_no_id_reason'),
            no_id_first_name=mother_fname,
            no_id_last_name=mother_lname,
            no_id_birthdate=mother_dob,
        )

