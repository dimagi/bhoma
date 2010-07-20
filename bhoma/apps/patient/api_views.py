from datetime import datetime
from django.http import HttpResponse
import json
from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient


def lookup_by_id(request):
    """
    Get a patient by ID, returning the json representation of the patient
    """
    pat_id = request.GET.get('id')
    patients = CPatient.view("patient/by_id", key=pat_id).all()
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
