"""
Module for processing patient data
"""
# use inner imports so we can handle processing okay
from bhoma.apps.encounter.models.couch import Encounter
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
from bhoma.apps.patient.models import CPatient
from bhoma.apps.case.util import get_or_update_bhoma_case,\
    close_missed_appointment_cases
from bhoma.apps.patient.encounters.config import CLASSIFICATION_CLINIC,\
    CLASSIFICATION_PHONE
from bhoma.apps.patient.encounters import config
from bhoma.apps.case.xform import extract_case_blocks
from bhoma.apps.case import const
from bhoma.utils.couch.database import get_db
from bhoma.apps.case.models.couch import PatientCase
import logging

def add_form_to_patient(patient_id, form):
    """
    Adds a clinic form to a patient, including all processing necessary.
    """
    
    patient = CPatient.get(patient_id)
    new_encounter = Encounter.from_xform(form)
    patient.encounters.append(new_encounter)
    
    encounter_info = ENCOUNTERS_BY_XMLNS.get(form.namespace)
    if not encounter_info:
        raise Exception("Attempt to add unknown form type: %s to patient %s!" % \
                        (form.namespace, patient_id))
    
    if encounter_info.classification == CLASSIFICATION_CLINIC:
        # process clinic form
        if encounter_info.is_routine_visit:
            # TODO: figure out what to do about routine visits (e.g. pregnancy)
            case = None
        else: 
            case = get_or_update_bhoma_case(form, new_encounter)
        if case:
            patient.cases.append(case)
        
        # also close any appointment cases we had open
        close_missed_appointment_cases(patient, form, new_encounter)
    elif encounter_info.classification == CLASSIFICATION_PHONE:
        # process phone form
        is_followup = form.namespace == config.CHW_FOLLOWUP_NAMESPACE
        if is_followup:
            caseblocks = extract_case_blocks(form)
            for caseblock in caseblocks:
                case_id = caseblock[const.CASE_TAG_ID]
                # find bhoma case 
                results = get_db().view("case/bhoma_case_lookup", key=case_id).one()
                if results:
                    raw_data = results["value"]
                    bhoma_case = PatientCase.wrap(raw_data)
                    for case in bhoma_case.commcare_cases:
                        if case.case_id == case_id:
                            # apply updates
                            case.update_from_block(caseblock)
                            # apply custom updates to bhoma case
                            if case.all_properties().get(const.CASE_TAG_BHOMA_CLOSE, None):
                                bhoma_case.closed = True
                                bhoma_case.outcome = case.all_properties().get(const.CASE_TAG_BHOMA_OUTCOME, "")
                                bhoma_case.closed_on = new_encounter.visit_date
                    # save
                    patient.update_cases([bhoma_case,])
    else:
        logging.error("Unknown classification %s for encounter: %s" % \
                      (encounter_info.classification, form.get_id))
    patient.save()
