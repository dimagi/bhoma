from bhoma.apps.patient.processing import add_new_clinic_form
from bhoma.apps.xforms.util import post_xform_to_couch
import os

def post_and_process_xform(filename, patient):
    doc = post_xform(filename, patient.get_id)    
    add_new_clinic_form(patient, doc)
    return doc
    
        
def post_xform(filename, patient_id):    
    file_path = os.path.join(os.path.dirname(__file__), "data", filename)
    xml_data = open(file_path, "rb").read()
    xml_data = xml_data.replace("REPLACE_PATID", patient_id)
    doc = post_xform_to_couch(xml_data)
    return doc
    
        