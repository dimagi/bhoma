from datetime import datetime
from django.http import HttpResponse
import json
import re
from dimagi.utils.web import render_to_response
from bhoma.apps.patient.models import CPatient
from dimagi.utils.couch.pagination import CouchPaginator
from bhoma.const import VIEW_PATIENT_BY_LAST_NAME, VIEW_PATIENT_BY_BHOMA_ID
from bhoma.apps.patient.util import restricted_patient_data
from bhoma.apps.patient import loader

@restricted_patient_data
def lookup_by_id(request):
    """
    Get a patient by ID, returning the json representation of the patient
    """
    pat_id = request.GET.get('id')
    if pat_id != None:
        patients = CPatient.view(VIEW_PATIENT_BY_BHOMA_ID, key=pat_id, reduce=False, include_docs=True).all()
        json_pats = [pat.to_json() for pat in patients]
        return HttpResponse(json.dumps(json_pats), mimetype='text/json')
    else:
        pat_uuid = request.GET.get('uuid')
        patient = loader.get_patient(pat_uuid)
        return HttpResponse(json.dumps(patient.to_json()), mimetype='text/json')

@restricted_patient_data
def fuzzy_match(request):
    # TODO this currently always returns nothing
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')
    # query = request.GET.get('q', '')
    # fpats = CPatient.view("patient/search", key=fname.lower(), include_docs=True)
    # lpats = CPatient.view("patient/search", key=lname.lower(), include_docs=True)
    return HttpResponse(json.dumps(None), mimetype='text/plain')


@restricted_patient_data
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
                patient.formatted_id,
                patient.gender,
                patient.birthdate.strftime("%Y-%m-%d") if patient.birthdate else "",
                patient.current_clinic_display]
    
    def id_formatter(id):
        """Strips any non-digits before processing the id"""
        return "".join(re.findall("\d+", id))
    
    paginator = CouchPaginator(VIEW_PATIENT_BY_BHOMA_ID, wrapper_func, 
                               search=True, search_preprocessor=id_formatter, 
                               view_args={"include_docs": True})
    return paginator.get_ajax_response(request)

@restricted_patient_data
def paging_identified(request):
    """
    Paging view, used by datatables url
    """
    
    def wrapper_func(row):
        """
        Given a row of the view, get out a json representation of a patient row
        """
        patient = CPatient.wrap(row["value"])
        return [patient.get_id,
                patient.formatted_id,
                patient.first_name,
                patient.last_name,
                patient.gender,
                patient.birthdate.strftime("%Y-%m-%d") if patient.birthdate else "",
                patient.current_clinic_display]

    paginator = CouchPaginator(VIEW_PATIENT_BY_LAST_NAME, wrapper_func, 
                               search=True, search_preprocessor=lambda x: x.lower())
    return paginator.get_ajax_response(request)

