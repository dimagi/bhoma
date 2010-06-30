from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required
from bhoma.apps.xforms.models.couch import CXFormInstance
from django.conf import settings
import bhoma.apps.xforms.views as xforms_views
from bhoma.apps.patient.encounters import registration
from bhoma.apps.patient.encounters.config import ACTIVE_ENCOUNTERS,\
    REGISTRATION_ENCOUNTER
from bhoma.apps.encounter.models import Encounter

def dashboard(request):
    patients = CPatient.view("patient/all")
    return render_to_response(request, "patient/dashboard.html", 
                              {"patients": patients} )
    
@login_required
def search(request):
    return render_to_response(request, "patient/search.html") 

def search_results(request):
    query = request.GET.get('q', '')
    if not query:
        return HttpResponseRedirect(reverse("patient_search"))
    patients = CPatient.view("patient/search", key=query.lower(), include_docs=True)
    minus_duplicates = SortedDict()
    for patient in patients:
        if not patient.get_id in minus_duplicates:
            minus_duplicates[patient.get_id] = patient
    return render_to_response(request, "patient/search_results.html", 
                              {"patients": minus_duplicates.values(), 
                               "query": query} ) 
                              
    
def new_patient(request):
    
    def callback(xform, doc):
        patient = registration.patient_from_instance(doc)
        patient.clinic_ids = [settings.BHOMA_CLINIC_ID,]
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient.get_id,)))  
    
    return xforms_views.play(request, REGISTRATION_ENCOUNTER.get_xform().id, callback)
    
                               
def single_patient(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = patient.encounters
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    encounter_types = ACTIVE_ENCOUNTERS
    return render_to_response(request, "patient/single_patient.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "encounter_types": encounter_types})
@login_required
def new_encounter(request, patient_id, encounter_slug):
    """A new encounter for a patient"""
    
    def callback(xform, doc):
        patient = CPatient.get(patient_id)
        patient.encounters.append(Encounter.from_xform(doc, encounter_slug))
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
    xform = ACTIVE_ENCOUNTERS[encounter_slug].get_xform()
    # TODO: generalize this better
    preloader_data = {"case": {"case-id" : patient_id},
                      "property": {"DeviceID": settings.BHOMA_CLINIC_ID },
                      "meta": {"UserID": request.user.get_profile()._id,
                               "UserName": request.user.username}}
                               
    return xforms_views.play(request, xform.id, callback, preloader_data)
    
                               
