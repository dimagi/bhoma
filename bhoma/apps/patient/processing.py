"""
Module for processing patient data
"""

def add_new_clinic_form(sender, patient_id, form, **kwargs):
    """
    Adds a clinic form to a patient, including all processing necessary.
    """
    # use inner imports so we can handle processing okay
    from bhoma.apps.encounter.models.couch import Encounter
    from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
    from bhoma.apps.patient.models import CPatient
    from bhoma.apps.case.util import get_or_update_bhoma_case
    
    patient = CPatient.get(patient_id)
    new_encounter = Encounter.from_xform(form)
    patient.encounters.append(new_encounter)
    
    encounter_info = ENCOUNTERS_BY_XMLNS.get(form.namespace)
    if not encounter_info:
        raise Exception("Attempt to add unknown form type: %s to patient %s!" % \
                        (form.namespace, patient_id))
    if encounter_info.is_routine_visit:
        # TODO: figure out what to do about routine visits (e.g. pregnancy)
        case = None
    else: 
        case = get_or_update_bhoma_case(form, new_encounter)
    if case:
        patient.cases.append(case)
    
    patient.save()