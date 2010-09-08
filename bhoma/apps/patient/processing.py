"""
Module for processing patient data
"""
# use inner imports so we can handle processing okay
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
from bhoma.apps.patient.models import CPatient
from bhoma.apps.case.util import get_or_update_bhoma_case,\
    close_previous_cases
from bhoma.apps.patient.encounters.config import CLASSIFICATION_CLINIC,\
    CLASSIFICATION_PHONE
from bhoma.apps.patient.encounters import config
from bhoma.apps.case.xform import extract_case_blocks
from bhoma.apps.case import const
from bhoma.utils.couch.database import get_db
from bhoma.apps.case.models import PatientCase
import logging
from bhoma.utils.parsing import string_to_datetime
from bhoma.apps.patient.signals import patient_updated
from bhoma.utils.logging import log_exception
from bhoma.apps.xforms.models import CXFormInstance
from bhoma.const import VIEW_ALL_PATIENTS
from datetime import datetime, time

def new_form_received(patient_id, form):
    """
    A new form was received for a patient.  This usually just adds the form
    to the patient object, but will fully reprocess the patient data if the
    form is from the past, so that previously-entered but later-occurring 
    changes can be applied to the data
    """
    patient = CPatient.get(patient_id)
    encounter_date = Encounter.get_visit_date(form)
    full_reprocess = False
    for encounter in patient.encounters:
        if encounter.visit_date > encounter_date:
            full_reprocess = True
            break
    
    if full_reprocess:
        reprocess(patient_id)
    else:
        add_form_to_patient(patient_id, form)
                
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
        close_previous_cases(patient, form, new_encounter)
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
                                bhoma_case.closed_on = datetime.combine(new_encounter.visit_date, time())
                    # save
                    patient.update_cases([bhoma_case,])
    else:
        logging.error("Unknown classification %s for encounter: %s" % \
                      (encounter_info.classification, form.get_id))
    patient.save()

def reprocess(patient_id):
    """
    Reprocess a patient's data from xforms, by playing them back in the order
    they are found.
    Returns true if successfully regenerated, otherwise false.
    """ 
    # you can't call the loader because the loader calls this
    patient = CPatient.view(VIEW_ALL_PATIENTS, key=patient_id).one()
    # first create a backup in case anything goes wrong
    backup_id = CPatient.copy(patient)
    try:
        # have to change types, otherwise we get conflicts with our cases
        backup = CPatient.get(backup_id)
        backup.doc_type = "PatientBackup"
        backup.save()
        
        # reload the original and blank out encounters/cases
        patient = CPatient.view(VIEW_ALL_PATIENTS, key=patient_id).one()
        patient.encounters = []
        patient.cases = []
        patient.backup_id = backup_id
        patient.save()
        
        patient_forms = CXFormInstance.view("patient/xforms", key=patient_id).all()
        
        def comparison_date(form):
            # get a date from the form
            return Encounter.get_visit_date(form)
            
        for form in sorted(patient_forms, key=comparison_date):
            encounter = ENCOUNTERS_BY_XMLNS.get(form.namespace)
            form_type = encounter.classification if encounter else CLASSIFICATION_PHONE
            add_form_to_patient(patient_id, form)
            patient_updated.send(sender=form_type, patient_id=patient_id)
        
        get_db().delete_doc(backup_id)
        return True
    except Exception, e:
        logging.error("problem regenerating patient case data: %s" % e)
        log_exception(e)
        current_rev = get_db().get_rev(patient_id)
        patient = get_db().get(backup_id)
        patient["_rev"] = current_rev
        patient["_id"] = patient_id
        patient["doc_type"] = "CPatient"
        get_db().save_doc(patient)
        get_db().delete_doc(backup_id)
        return False