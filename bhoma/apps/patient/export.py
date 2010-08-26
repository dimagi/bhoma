from bhoma.apps.patient.models.couch import CPatient
import json
from bhoma.utils.couch.database import get_db
import tempfile
import zipfile
from django.core.servers.basehttp import FileWrapper

def get_id(doc):
    if "_id" in doc:  return doc["_id"]
    elif "id" in doc: return doc["id"]
    return ""

def export_patient(patient_id):
    """
    Exports a patient and all their forms, returning a handle to a temporary file object
    """
    pat = CPatient.get(patient_id)
    patient_data = json.dumps(pat.to_json())
    patient_forms = get_db().view("patient/xforms", key=patient_id).all()
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    # write raw patient data
    archive.writestr("patient_%s.json" % patient_id, patient_data)
    for form in patient_forms:
        archive.writestr("patient_form_%s.json" % get_id(form), json.dumps(form))
    archive.close()
    temp.seek(0)    
    return temp

def import_patient(filename):
    """From a handle to a zip file, import patient data"""
    archive = zipfile.ZipFile(filename, 'r', zipfile.ZIP_DEFLATED)
    items = archive.infolist()
    docs = [json.loads(archive.read(item)) for item in items]
    
    
    for doc in docs:
        if get_db().doc_exist(get_id(doc)):
            get_db().save_doc(doc, force_update=True)
        else:
            try:
                doc.pop("_rev")
            except KeyError: pass
            get_db().save_doc(doc, force_update=True)
        
    