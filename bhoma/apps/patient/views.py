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
    REGISTRATION_ENCOUNTER, get_active_encounters
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.case.xform import get_or_update_cases
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions

def test(request):
    template = request.GET["template"] if "template" in request.GET \
                                       else "touchscreen/example-inner.html"
    header = request.GET["header"] if "header" in request.GET \
                                   else "Hello World!"
    return render_to_response(request, "touchscreen/wrapper-dynamic.html", 
                              {"header": header,
                               "template": template,
                               "options": TouchscreenOptions.default()})

@login_required
def dashboard(request):
    patients = CPatient.view("patient/all")
    return render_to_response(request, "patient/dashboard.html", 
                              {"patients": patients} )
    
@login_required
def search(request):
    return render_to_response(request, "patient/search.html") 

@login_required
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
                              
    
@login_required
def new_patient(request):
    
    def callback(xform, doc):
        patient = registration.patient_from_instance(doc)
        patient.clinic_ids = [settings.BHOMA_CLINIC_ID,]
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient.get_id,)))  
    
    return xforms_views.play(request, REGISTRATION_ENCOUNTER.get_xform().id, callback)

@login_required                
def single_patient(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = patient.encounters
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    encounter_types = get_active_encounters(patient)
    options = TouchscreenOptions.default()
    # TODO: are we upset about how this breaks MVC?
    options.menubutton.show  = False
    options.nextbutton = ButtonOptions(text="NEW FORM", 
                                       link=reverse("choose_new_patient_encounter", 
                                                    args=[patient_id]))
    return render_to_response(request, "patient/single_patient_touchscreen.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "encounter_types": encounter_types,
                               "options": options })

@login_required
def choose_new_encounter(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounter_types = get_active_encounters(patient)
    # TODO: are we upset about how this breaks MVC?
    options = TouchscreenOptions.default()
    options.menubutton.show=False
    options.nextbutton.show=False
    return render_to_response(request, "patient/choose_encounter_touchscreen.html", 
                              {"patient": patient,
                               "encounter_types": encounter_types,
                               "options": options })

@login_required
def new_encounter(request, patient_id, encounter_slug):
    """A new encounter for a patient"""
    
    def callback(xform, doc):
        patient = CPatient.get(patient_id)
        new_encounter = Encounter.from_xform(doc, encounter_slug)
        patient.encounters.append(new_encounter)
        # touch our cases too
        touched_cases = get_or_update_cases(doc)
        patient.update_cases(touched_cases.values())
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
    
    xform = ACTIVE_ENCOUNTERS[encounter_slug].get_xform()
    # TODO: generalize this better
    preloader_data = {"case": {"case-id" : patient_id},
                      "meta": {"clinic_id": settings.BHOMA_CLINIC_ID,
                               "user_id":   request.user.get_profile()._id,
                               "username":  request.user.username}}
                               
    return xforms_views.play(request, xform.id, callback, preloader_data)
    
                               
