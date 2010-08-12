"""
Module for processing patient data
"""
from bhoma.apps.encounter.models.couch import Encounter
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.drugs.models import Drug

def add_new_clinic_form(patient, xform_doc):
    """
    Adds a form to a patient, including all processing necessary.
    """
    """
    Find out if drug prescribed, identify types prescribed and formulation
    """    
    if "drugs" in xform_doc and "prescribed" in xform_doc["drugs"] and "med" in xform_doc["drugs"]["prescribed"]:
        xform_doc.drugs_prescribed = []
        #need to put med object as list if only one, ok as dictionary if more
        def extract_drugs(doc):
            drugs = xform_doc["drugs"]["prescribed"]["med"]
            if "duration" in drugs:
                return [drugs]
            return drugs
        xform_drugs = extract_drugs(xform_doc)
        for each_drug in xform_drugs:

            #find drug from drill down options on xform
            drug = each_drug["drug_prescribed"]
            formulation_prescribed = each_drug["drug_formulation"]
            dbdrug = Drug.objects.get(slug=drug)
            
            #check the formulation prescribed is possible
            formulations_checked = []
            types_checked = []
            for formulation in dbdrug.formulations.all():
                if formulation_prescribed == formulation.name: 
                    formulations_checked = formulation_prescribed
                    break
                else:
                    formulations_checked = ["other"]
            for type in dbdrug.types.all(): types_checked.append(type.name)
            
            xform_doc.drugs_prescribed.append({"types": types_checked,"formulation": formulations_checked})
    
    xform_doc.save()  
    
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
    patient.save()
    