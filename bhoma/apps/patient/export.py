from bhoma.apps.patient.models.couch import CPatient
import json
from bhoma.utils.couch.database import get_db
import tempfile
import zipfile
from django.core.servers.basehttp import FileWrapper
from bhoma.apps.xforms.util import post_xform_to_couch
from bhoma.apps.patient.processing import new_form_workflow
from bhoma.apps.patient.signals import SENDER_EXPORT

def get_id(doc):
    if "_id" in doc:  return doc["_id"]
    elif "id" in doc: return doc["id"]
    return ""

def get_zip_filename(patient):
    return ("%s_%s.zip" % (patient.first_name, patient.last_name)).lower()

def get_form_filename(count, form):
    return "%03d_%s.xml" % (count, form.type)

def get_patient_filename(patient):
    return "patient.json"

def export_patient(pat):
    """
    Exports a patient and all their forms, returning a handle to a temporary file object
    """
    
    # clear dynamic data
    pat.encounters = []
    pat.cases = []
    pat.pregnancies = []
    patient_data = json.dumps(pat.to_json())
    
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    
    # write raw patient data
    archive.writestr(get_patient_filename(pat), patient_data)
    
    # write forms
    count = 1
    for form in pat.xforms():
        archive.writestr(get_form_filename(count, form), form.get_xml())
        count += 1
    archive.close()
    temp.seek(0)
    return temp

def import_patient_json_file(filename):
    """
    From a handle to a json file, import patient data.
    Returns the newly created patient.
    This will OVERRIDE any existing patient with the same ID.
    and DELETE ALL FORMS ASSOCIATED WITH THE PATIENT.
    """
    with open(filename, "r") as json_file:
        return import_patient_json(json.loads(json_file.read()))
    
def import_patient_json(pat_data):
    """
    From a handle to a json file, import patient data.
    Returns the newly created patient.
    This will OVERRIDE any existing patient with the same ID.
    and DELETE ALL FORMS ASSOCIATED WITH THE PATIENT.
    """
    id = get_id(pat_data)
    if get_db().doc_exist(id):
        get_db().save_doc(pat_data, force_update=True)
    else:
        try:
            pat_data.pop("_rev")
        except KeyError: pass
        get_db().save_doc(pat_data, force_update=True)
    pat = CPatient.get(id)
    for form in pat.xforms():
        form.delete()
    return pat

def add_form_file_to_patient(patient_id, filename):
    """
    From a handle to a patient and xform instance xml file, 
    add that form to the patient.
    Returns the updated patient and newly created form.
    This will OVERRIDE any existing form with the same ID.
    """
    with open(filename, "r") as f:
        return add_form_to_patient(patient_id, f.read())
    
def add_form_to_patient(patient_id, form):
    """
    From a handle to a patient and xform instance xml, 
    add that form to the patient.
    Returns the updated patient and newly created form.
    This will OVERRIDE any existing form with the same ID.
    """
    formdoc = post_xform_to_couch(form)
    new_form_workflow(formdoc, SENDER_EXPORT, patient_id)
    return CPatient.get(patient_id), formdoc

def import_patient_zip(filename):
    """From a handle to a zip file, import patient data"""
    archive = zipfile.ZipFile(filename, 'r', zipfile.ZIP_DEFLATED)
    items = archive.infolist()
    patient_json, formlist = items[0], items[1:]
    pat_data = json.loads(archive.read(patient_json))
    patient = import_patient_json(pat_data)
    
    for form in formlist:
        form = archive.read(form)
        pat, formdoc = add_form_to_patient(patient.get_id, form)
    return pat