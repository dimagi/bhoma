"""
Module for processing patient data
"""
from bhoma.apps.encounter.models.couch import Encounter
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.reports.calc.pregnancy import extract_pregnancies
from bhoma.apps.reports.models import CPregnancy

def add_new_clinic_form(patient, xform_doc):
    """
    Adds a form to a patient, including all processing necessary.
    """
    new_encounter = Encounter.from_xform(xform_doc)
    encounter_info = ENCOUNTERS_BY_XMLNS.get(xform_doc.namespace)
    if not encounter_info:
        raise Exception("Attempt to add unknown form type: %s to patient %s!" % \
                        xform_doc.namespace, patient.get_id)
    patient.encounters.append(new_encounter)
    
    if encounter_info.is_routine_visit:
        # TODO: figure out what to do about routine visits (e.g. pregnancy)
        case = None
    else: 
        case = get_or_update_bhoma_case(xform_doc, new_encounter)
    if case:
        patient.cases.append(case)
    
    pregs = extract_pregnancies(patient)
    # manually remove old pregnancies, since all pregnancy data is dynamically generated
    for old_preg in CPregnancy.view("reports/pregnancies_for_patient", key=patient.get_id).all():
        old_preg.delete() 
    for preg in pregs:
        couch_pregnancy = preg.to_couch_object()
        couch_pregnancy.save()
    patient.save()
    