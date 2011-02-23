from bhoma.apps.patient.encounters import config
from bhoma.apps.case.util import jr_float_to_string_int

def process_referral(patient, new_encounter):
    form = new_encounter.get_xform()
    assert form.namespace == config.CHW_REFERRAL_NAMESPACE
    bhoma_id = form.xpath("patient_id")
    if bhoma_id:
        # TODO: find patient bhoma id, 
        str_id = jr_float_to_string_int(bhoma_id)
        raise Exception("we need a way to make the form/patient lookup happen earlier than this")
        #we need a way to make the form/patient lookup happen earlier than this")
        #in the processing workflow
        # lookup patient
        # create bhoma case
        # check life threatening
        