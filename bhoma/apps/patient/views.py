from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.patient.forms import PatientForm
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required
from bhoma.apps.patient.encounters.registration import RegistrationEncounter
from bhoma.apps.xforms.models.couch import CXFormInstance

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
    
    patient = None
    
    if request.POST:
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            return HttpResponseRedirect(reverse("patient_dashboard"))  
    else:
        form = PatientForm()
        
    return render_to_response(request, "patient/new_patient.html", 
                              {"form": form,
                               "patient": patient })
                                
                               
def single_patient(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = Encounter.view("encounter/by_patient", key=patient.get_id, include_docs=True)
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    types = [RegistrationEncounter()]
    return render_to_response(request, "patient/single_patient.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "types": types})

def form_complete(request, patient_id, form_id):
    print patient_id
    print form_id
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = Encounter.view("encounter/by_patient", key=patient.get_id, include_docs=True)
    types = [RegistrationEncounter()]
    return render_to_response(request, "patient/single_patient.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "types": types})
