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
from bhoma.utils.couch.database import get_db
import logging
from bhoma.apps.patient.signals import patient_updated
from bhoma.utils.logging import log_exception
from bhoma.apps.xforms.models import CXFormInstance
from bhoma.const import VIEW_ALL_PATIENTS
from bhoma.apps.case.bhomacaselogic.chw.followup import process_phone_form
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import is_pregnancy_encounter
from bhoma.apps.case.bhomacaselogic.pregnancy.pregnancy import update_pregnancies
from bhoma.apps.case.bhomacaselogic.pregnancy.case import update_pregnancy_cases
from bhoma.apps.case.bhomacaselogic.shared import get_patient_id_from_form


def new_form_workflow(doc, sender, patient_id=None):
    """
    The shared workflow that is called any time a new form is received
    (either from the phone, touchscreen, or some import/export utilities)
    """
    if not doc.has_duplicates():
        if not patient_id:
            patient_id = get_patient_id_from_form(doc)
        if patient_id:
            new_form_received(patient_id=patient_id, form=doc)
            patient_updated.send(sender=sender, patient_id=patient_id)
    
    

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
        case = get_or_update_bhoma_case(form, new_encounter)
        if case:
            patient.cases.append(case)
        
        # also close any previous cases we had open, according
        # to the complicated rules
        close_previous_cases(patient, form, new_encounter)
        
        if is_pregnancy_encounter(new_encounter):
            update_pregnancies(patient, new_encounter)
            update_pregnancy_cases(patient, new_encounter)
            
    elif encounter_info.classification == CLASSIFICATION_PHONE:
        # process phone form
        is_followup = form.namespace == config.CHW_FOLLOWUP_NAMESPACE
        if is_followup:
            process_phone_form(patient, new_encounter)
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
        
        # reload the original and blank out encounters/cases/version 
        patient = CPatient.view(VIEW_ALL_PATIENTS, key=patient_id).one()
        patient.encounters = []
        patient.cases = []
        patient.pregnancies = []
        patient.backup_id = backup_id
        patient.app_version = None # blanking out the version marks it "upgraded" to the current version
        patient.save()
        
        for form in patient.unique_xforms():
            encounter = ENCOUNTERS_BY_XMLNS.get(form.namespace)
            form_type = encounter.classification if encounter else CLASSIFICATION_PHONE
            add_form_to_patient(patient_id, form)
            patient_updated.send(sender=form_type, patient_id=patient_id)
            # save to stick the new version on so we know we've upgraded this form
            if form.requires_upgrade():
                form.save()
        
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