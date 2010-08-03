from datetime import datetime
from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient, CPhone
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required
import json
from bhoma.apps.xforms.models import CXFormInstance
from django.conf import settings
import bhoma.apps.xforms.views as xforms_views
from bhoma.apps.patient.encounters import registration
from bhoma.apps.patient.encounters.config import ACTIVE_ENCOUNTERS,\
    REGISTRATION_ENCOUNTER, get_active_encounters
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions
from bhoma.apps.patient.encounters.registration import patient_from_instance
from bhoma.apps.patient.models import CAddress
from bhoma.utils.parsing import string_to_boolean

def test(request):
    dynamic = string_to_boolean(request.GET["dynamic"]) if "dynamic" in request.GET else True
    template = request.GET["template"] if "template" in request.GET \
                                       else "touchscreen/example-inner.html"
    header = request.GET["header"] if "header" in request.GET \
                                   else "Hello World!"
    pat_id = request.GET["id"] if "id" in request.GET \
                               else "000000000001" 
    try:
        patient = CPatient.view("patient/by_id", key=pat_id).one()
    except:
        patient = None
    if dynamic:
        return render_to_response(request, "touchscreen/wrapper-dynamic.html", 
                                  {"header": header,
                                   "template": template,
                                   "patient": patient,
                                   "options": TouchscreenOptions.default()})
    else:
        return render_to_response(request, template, 
                              {"patient": patient,
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
                              
    
def single_patient(request, patient_id):
    patient = CPatient.view("patient/all", key=patient_id).one()
    encounters = patient.encounters
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    encounter_types = get_active_encounters(patient)
    options = TouchscreenOptions.default()
    # TODO: are we upset about how this breaks MVC?
    options.nextbutton.show  = False
    options.backbutton = ButtonOptions(text="BACK", 
                                       link=reverse("patient_select"))
    
    # TODO: figure out a way to do this more centrally
    # Inject cases into encounters so we can show them linked in the view
    for encounter in patient.encounters:
        for case in patient.cases:
            if case.encounter_id == encounter.get_id:
                encounter.dynamic_data["case"] = case
            
    return render_to_response(request, "patient/single_patient_touchscreen.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "encounter_types": encounter_types,
                               "options": options })

@login_required
def choose_new_encounter(request, patient_id):
    # no longer used.
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
        case = get_or_update_bhoma_case(doc, new_encounter)
        if case:
            patient.cases.append(case)
        # touch our cases too
        # touched_cases = get_or_update_cases(doc)
        # patient.update_cases(touched_cases.values())
        patient.save()
        return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
    
    xform = ACTIVE_ENCOUNTERS[encounter_slug].get_xform()
    # TODO: generalize this better
    preloader_data = {"case": {"patient_id" : patient_id},
                      "meta": {"clinic_id": settings.BHOMA_CLINIC_ID,
                               "user_id":   request.user.get_profile()._id,
                               "username":  request.user.username}}
                               
    return xforms_views.play(request, xform.id, callback, preloader_data)
    


def patient_select(request):
    """
    Entry point for patient select/registration workflow
    """
    if request.method == "POST":
        # TODO: handle + redirect
        # {'new': True, 'patient': { <patient_blob> } 
        data = json.loads(request.POST.get('result'))
        create_new = data.get("new")
        pat_dict = data.get("patient")
        if create_new:
            
            # Here's an example format:
            # u'patient': {u'dob': u'2000-02-02', u'sex': u'm', 
            #              u'lname': u'alskdjf', u'phone': None, 
            #              u'fname': u'f8rask', u'village': u'PP'f, 
            #              u'dob_est': False, u'id': u'727272727272'}}
            # 
            def map_basic_data(pat_dict):
                # let's use the same keys, for now this will have to suffice
                new_dict = {}
                mapping = (("dob",  "birthdate"), 
                           ("fname",  "first_name"),
                           ("lname",  "last_name"),
                           ("dob_est",  "birthdate_estimated"),
                           ("sex",  "gender"),
                           ("id",  "patient_id")
                           )
                for oldkey, newkey in mapping:
                    new_dict[newkey] = pat_dict[oldkey]
                return new_dict
            clean_data = map_basic_data(pat_dict)
            patient = patient_from_instance(clean_data)
            patient.phones=[CPhone(is_default=True, number=pat_dict["phone"])]
            # TODO: create an enocounter for this reg
            patient.address = CAddress(village=pat_dict["village"], 
                                       clinic_id=settings.BHOMA_CLINIC_ID,
                                       zone=pat_dict["chw_zone"])
            patient.clinic_ids = [settings.BHOMA_CLINIC_ID,]
            
            patient.save()
            return HttpResponseRedirect(reverse("single_patient", args=(patient.get_id,)))
        elif pat_dict is not None:
            # we get a real couch patient object in this case
            pat_uid = pat_dict["_id"]
            return HttpResponseRedirect(reverse("single_patient", args=(pat_uid,)))
        
    return render_to_response(request, "xforms/touchscreen.html", 
                              {'form': {'name': 'patient reg', 
                                        'wfobj': 'wfGetPatient'}, 
                               'mode': 'workflow',
                               'dynamic_scripts': ["webapp/javascripts/patient_reg.js",] })
    
def render_content (request, template):
    if template == 'single-patient':
        pat_uuid = request.POST.get('uuid')
        patient = CPatient.view("patient/all", key=pat_uuid).one()
        return render_to_response(request, 'patient/single_patient_block.html', {'patient': patient})
    else:
        #error
        pass

# import our api views so they can be referenced normally by django.
# this is just a code cleanliness issue
from api_views import *
