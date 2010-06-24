from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.patient.forms import PatientForm
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required
from bhoma.apps.xforms.models.couch import CXFormInstance
from django.conf import settings
import bhoma.apps.xforms.views as xforms_views
from bhoma.apps.patient.encounters import registration

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
        patient.clinic_id = settings.BHOMA_CLINIC_ID
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient.get_id,)))  
    
    return xforms_views.play(request, registration.get_xform().id, callback)
    
                               
def single_patient(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = Encounter.view("encounter/by_patient", key=patient.get_id, include_docs=True)
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    # types = [RegistrationEncounter()]
    types = []
    return render_to_response(request, "patient/single_patient.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "types": types})

