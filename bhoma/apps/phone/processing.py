from bhoma.apps.case.models.couch import PatientCase
from bhoma.apps.patient.encounters import config
from bhoma.apps.case.xform import extract_case_blocks
from bhoma.apps.case import const
from bhoma.apps.xforms import const as xforms_const
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.encounter.models.couch import Encounter
    
def get_patient_from_form(form):
    # this is how I would like this to be implemented but it's not there yet
    patient_id = form.xpath("case/patient_id")
    if patient_id:
        return CPatient.get(patient_id)
    return None
            
def add_new_phone_form(sender, patient_id, form, **kwargs):
    
    patient = CPatient.get(patient_id)
    new_encounter = Encounter.from_xform(form)
    patient.encounters.append(new_encounter)
    patient.save()
    
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
                            bhoma_case.closed_on = case.modified_on
                # save
                patient.update_cases([bhoma_case,])
                patient.save()
    
    
    pass