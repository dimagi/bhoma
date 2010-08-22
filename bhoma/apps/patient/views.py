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
from bhoma.apps.patient.encounters.config import ACTIVE_ENCOUNTERS, get_encounters
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.case.util import get_or_update_bhoma_case
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions
from bhoma.apps.patient.encounters.registration import patient_from_instance
from bhoma.apps.patient.models import CAddress
from bhoma.utils.parsing import string_to_boolean
from bhoma.apps.patient.processing import add_new_clinic_form
from bhoma.utils.couch.database import get_db
import tempfile
import zipfile
from bhoma.apps.patient import export
from bhoma.apps.reports.calc import pregnancy
from bhoma.utils.couch import uid
from bhoma.utils.logging import log_exception
import logging

def test(request):
    dynamic = string_to_boolean(request.GET["dynamic"]) if "dynamic" in request.GET else True
    template = request.GET["template"] if "template" in request.GET \
                                       else "touchscreen/example-inner.html"
    header = request.GET["header"] if "header" in request.GET \
                                   else "Hello World!"
    pat_id = request.GET["id"] if "id" in request.GET \
                               else "000000000001" 
    try:
        patient = CPatient.view("patient/all", key=pat_id).one()
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
    xforms = CXFormInstance.view("patient/xforms", key=patient.get_id, include_docs=True)
    encounter_types = get_encounters(patient)
    options = TouchscreenOptions.default()
    # TODO: are we upset about how this breaks MVC?
    options.nextbutton.show  = False
    options.backbutton = ButtonOptions(text="BACK", 
                                       link=reverse("patient_select"))
    
    encounters = sorted(patient.encounters, key=lambda encounter: encounter.visit_date, reverse=True)
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

def export_patient(request, patient_id):
    """
    Export a patient object to a file.
    """
    # this may not perform with huge amounts of data, but for a single patient should be fine
    temp_file = export.export_patient(patient_id)
    data = temp_file.read()
    response = HttpResponse(data, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=bhoma-patient-%s.zip' % patient_id
    response['Content-Length'] = len(data)
    return response

def regenerate_data(request, patient_id):
    """
    Regenerate all patient data, by reprocessing all forms.
    """
    patient = CPatient.view("patient/all", key=patient_id).one()
    # first create a backup in case anything goes wrong
    backup_id = CPatient.copy(patient)
    try: 
        # reload the original and blank out encounters/cases
        patient = CPatient.view("patient/all", key=patient_id).one()
        patient.encounters = []
        patient.cases = []
        patient.backup_id = backup_id
        patient.save()
        
        patient_forms = CXFormInstance.view("patient/xforms", key=patient_id).all()
        for form in patient_forms:
            add_new_clinic_form(patient, form)
        get_db().delete_doc(backup_id)
    except Exception, e:
        logging.error("problem regenerating patient case data: %s" % e)
        log_exception(e)
        current_rev = get_db().get_rev(patient_id)
        patient = get_db().get(backup_id)
        patient["_rev"] = current_rev
        patient["_id"] = patient_id
        get_db().save_doc(patient)
        get_db().delete_doc(backup_id)
        
    return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
    
    
@login_required
def new_encounter(request, patient_id, encounter_slug):
    """A new encounter for a patient"""
    encounter_info = ACTIVE_ENCOUNTERS[encounter_slug]
    
    def callback(xform, doc):
        if doc != None:
            patient = CPatient.get(patient_id)
            add_new_clinic_form(patient, doc)
        return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
    
    xform = encounter_info.get_xform()
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

        if not data:
            return HttpResponseRedirect('/')
        elif create_new:
            
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
                               'dynamic_scripts': ["patient/javascripts/patient_reg.js",] })
    
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
