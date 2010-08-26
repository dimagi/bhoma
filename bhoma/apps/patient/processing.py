"""
Module for processing patient data
"""

def add_new_clinic_form(sender, patient, form, **kwargs):
    """
    Adds a clinic form to a patient, including all processing necessary.
    """
    # use inner imports so we can handle processing okay
    from bhoma.apps.encounter.models.couch import Encounter
    from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
    from bhoma.apps.case.util import get_or_update_bhoma_case
    
    new_encounter = Encounter.from_xform(form)
    encounter_info = ENCOUNTERS_BY_XMLNS.get(form.namespace)
    if not encounter_info:
        raise Exception("Attempt to add unknown form type: %s to patient %s!" % \
                        form.namespace, patient.get_id)
    patient.encounters.append(new_encounter)
    
    if encounter_info.is_routine_visit:
        # TODO: figure out what to do about routine visits (e.g. pregnancy)
        case = None
    else: 
        case = get_or_update_bhoma_case(form, new_encounter)
    if case:
        patient.cases.append(case)
    