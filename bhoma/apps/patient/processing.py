"""
Module for processing patient data
"""
from bhoma.apps.encounter.models.couch import Encounter
from bhoma.apps.patient.encounters.config import ENCOUNTERS_BY_XMLNS
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.drugs.models import Drug
from bhoma.apps.reports.calc.pregnancy import extract_pregnancies
from bhoma.apps.patient.models.couch import ReportContribution
from bhoma.apps.reports.models import CPregnancy
from bhoma.apps.zscore.models import Zscore
from math import pow

def add_new_clinic_form(patient, xform_doc):
    """
    Adds a form to a patient, including all processing necessary.
    """
    
    """For Under5, hook up zscore calculated"""
    if xform_doc["#type"] == "underfive" and patient.age_in_months <= 60:
        xform_doc.zscore_calc_good = []
        zscore = Zscore.objects.get(gender=patient.gender, age=patient.age_in_months)
        if xform_doc["nutrition"]["weight_for_age"] and xform_doc["vitals"]["weight"]:
            def calculate_zscore(l_value,m_value,s_value,x_value):
                #for L != 0, Z = (((X/M)^L)-1)/(L*S)
                eval_power = pow((float(x_value) / m_value),l_value)
                return ((eval_power - 1) / (l_value * s_value))
            
            def compare_sd(zscore_value):
                if zscore_value >= 0: 
                    return "0"
                elif 0 > zscore_value and zscore_value >= -2: 
                    return "-2"
                elif -2 > zscore_value and zscore_value >= -3: 
                    return "-3"
                elif -3 > zscore_value:
                    return "below -3"
            
            zscore_num = calculate_zscore(zscore.l_value, zscore.m_value, zscore.s_value, xform_doc["vitals"]["weight"])
            sd_num = compare_sd(zscore_num)
            
            if xform_doc["nutrition"]["weight_for_age"] == sd_num:
                xform_doc.zscore_calc_good = "true"
            else:
                xform_doc.zscore_calc_good = "false"       
        
        xform_doc.save()
    
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
            
            xform_doc.drugs_prescribed.append({"name": dbdrug.slug, "types": types_checked,"formulation": formulations_checked})
    
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
    
    pregs = extract_pregnancies(patient)
    # manually remove old pregnancies, since all pregnancy data is dynamically generated
    for old_preg in CPregnancy.view("reports/pregnancies_for_patient", key=patient.get_id).all():
        old_preg.delete() 
    for preg in pregs:
        couch_pregnancy = preg.to_couch_object()
        couch_pregnancy.save()
    patient.save()
    