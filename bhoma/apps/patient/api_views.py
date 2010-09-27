from datetime import datetime
from django.http import HttpResponse
import json
from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient
from bhoma.utils.couch.pagination import CouchPaginator
from bhoma.const import VIEW_ALL_PATIENTS, VIEW_PATIENT_SEARCH,\
    VIEW_PATIENT_BY_LAST_NAME


def lookup_by_id(request):
    """
    Get a patient by ID, returning the json representation of the patient
    """
    pat_id = request.GET.get('id')
    patients = CPatient.view("patient/by_bhoma_id", key=pat_id).all()
    json_pats = [pat.to_json() for pat in patients]
    return HttpResponse(json.dumps(json_pats), mimetype='text/json')

def fuzzy_match(request):
    # TODO this currently always returns nothing
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')
    # query = request.GET.get('q', '')
    # fpats = CPatient.view("patient/search", key=fname.lower(), include_docs=True)
    # lpats = CPatient.view("patient/search", key=lname.lower(), include_docs=True)
    return HttpResponse(json.dumps(None), mimetype='text/plain')


def paging(request):
    """
    Paging view, used by datatables url
    """
    
    def wrapper_func(row):
        """
        Given a row of the view, get out a json representation of a patient row
        """
        patient = CPatient.wrap(row["value"])
        return [patient.get_id,
                patient.first_name,
                patient.last_name,
                patient.gender,
                patient.birthdate.strftime("%Y-%m-%d") if patient.birthdate else "",
                patient.formatted_id,
                ", ".join(patient.clinic_ids)]
        
    paginator = CouchPaginator(VIEW_PATIENT_BY_LAST_NAME, wrapper_func, 
                               search=True)
    return paginator.get_ajax_response(request)
