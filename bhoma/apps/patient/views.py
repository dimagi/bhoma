from datetime import datetime
from bhoma.utils import render_to_response
from bhoma.apps.patient.models import CPatient, CPhone
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.contrib.auth.decorators import login_required, permission_required,\
    user_passes_test
import json
from bhoma.apps.xforms.models import CXFormInstance
from django.conf import settings
import bhoma.apps.xforms.views as xforms_views
from bhoma.apps.patient.encounters.config import CLINIC_ENCOUNTERS, get_encounters,\
    ENCOUNTERS_BY_XMLNS, get_classification, CLASSIFICATION_PHONE,\
    CHW_ENCOUNTERS
from bhoma.apps.encounter.models import Encounter
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions,\
    ButtonOptions
from bhoma.apps.patient.encounters.registration import patient_from_instance
from bhoma.apps.patient.models import CAddress
from bhoma.apps.patient.util import restricted_patient_data
from bhoma.utils.parsing import string_to_boolean, string_to_datetime
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient import export, loader
from bhoma.utils.couch import uid
from bhoma.utils.logging import log_exception
import logging
from bhoma.apps.patient.signals import SENDER_CLINIC
from bhoma.apps.patient.processing import add_form_to_patient, reprocess,\
    new_form_received, new_form_workflow
from bhoma.const import VIEW_ALL_PATIENTS

@restricted_patient_data
def test(request):
    dynamic = string_to_boolean(request.GET["dynamic"]) if "dynamic" in request.GET else True
    template = request.GET["template"] if "template" in request.GET \
                                       else "touchscreen/example-inner.html"
    header = request.GET["header"] if "header" in request.GET \
                                   else "Hello World!"
    pat_id = request.GET["id"] if "id" in request.GET \
                               else "000000000001" 
    try:
        patient = loader.get_patient(pat_id)
    except Exception:
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


@restricted_patient_data
def dashboard(request):
    return render_to_response(request, "patient/dashboard.html",{} ) 

@restricted_patient_data
def dashboard_identified(request):
    return render_to_response(request, "patient/dashboard_identified.html",{} ) 
                              
    
def search(request):
    return render_to_response(request, "patient/search.html") 

@restricted_patient_data
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
                              
    
@restricted_patient_data
def single_patient(request, patient_id):
    patient = loader.get_patient(patient_id)
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
        if encounter.get_xform():
            encounter.dynamic_data["classification"] = get_classification(encounter.get_xform().namespace)
            encounter.dynamic_data["cases"] = []
            for case in patient.cases:
                if case.encounter_id == encounter.get_id:
                    encounter.dynamic_data["cases"].append(case)
        
    
    return render_to_response(request, "patient/single_patient_touchscreen.html", 
                              {"patient": patient,
                               "encounters": encounters,
                               "xforms": xforms,
                               "encounter_types": encounter_types,
                               "options": options })

@restricted_patient_data
@permission_required("webapp.bhoma_enter_data")
def edit_patient(request, patient_id):
    if request.method == "POST":
        data = json.loads(request.POST.get('result'))
        patinfo = data.get('patient')

        if patinfo:
            #this is all quite similar to creating a new patient; the code should probably be
            #consolidated

            patient = loader.get_patient(patinfo['_id'])
            patient.first_name = patinfo['fname']
            patient.last_name = patinfo['lname']
            patient.birthdate = string_to_datetime(patinfo['dob']).date() if patinfo['dob'] else None
            patient.birthdate_estimated = patinfo['dob_est']
            patient.gender = patinfo['sex']

            if patinfo.get('phone'):
                patient.phones = [CPhone(is_default=True, number=patinfo['phone'])]
            else:
                patient.phones = []
            
            patient.address = CAddress(village=patinfo.get('village'), 
                                       clinic_id=settings.BHOMA_CLINIC_ID,
                                       zone=patinfo['chw_zone'],
                                       zone_empty_reason=patinfo['chw_zone_na'])
            patient.save()

        return HttpResponseRedirect(reverse("single_patient", args=(data.get('_id'),)))

    return render_to_response(request, "bhoma_touchscreen.html", 
                              {'form': {'name': 'patient edit', 
                                        'wfobj': 'wfEditPatient',
                                        'wfargs': json.dumps(patient_id)}, 
                               'mode': 'workflow',
                               'dynamic_scripts': ["patient/javascripts/patient_reg.js",] })

@restricted_patient_data
def export_data(request):
    return render_to_response(request, "patient/export_data.html",
                              {"clinic_encounters": CLINIC_ENCOUNTERS,
                               "chw_encounters": CHW_ENCOUNTERS})
    
@restricted_patient_data
def export_all_data(request):
    return HttpResponse("Aw shucks, that's not ready yet.  Please download the forms individually")
    
@restricted_patient_data
def export_patient(request, patient_id):
    patient = CPatient.get(patient_id)
    count = 1
    form_filenames = []
    for form in patient.xforms():
        form_filenames.append(export.get_form_filename(count,  form))
        count += 1
    return render_to_response(request, "patient/export_instructions.html", 
                              {"patient": patient,
                               "zip_filename": export.get_zip_filename(patient),
                               "foldername": export.get_zip_filename(patient).split(".")[0],
                               "pat_filename": export.get_patient_filename(patient),
                               "forms": form_filenames})

@restricted_patient_data
def export_patient_download(request, patient_id):
    """
    Export a patient's forms to a zip file.
    """
    # this may not perform with huge amounts of data, but for a single 
    # patient should be fine
    patient = CPatient.get(patient_id)
    temp_file = export.export_patient(patient)
    data = temp_file.read()
    response = HttpResponse(data, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % export.get_zip_filename(patient)
    response['Content-Length'] = len(data)
    return response

@restricted_patient_data
def regenerate_data(request, patient_id):
    """
    Regenerate all patient data, by reprocessing all forms.
    """
    reprocess(patient_id)    
    return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  
    
@restricted_patient_data
@permission_required("webapp.bhoma_enter_data")
def new_encounter(request, patient_id, encounter_slug):
    """A new encounter for a patient"""
    encounter_info = CLINIC_ENCOUNTERS[encounter_slug]
    
    def callback(xform, doc):
        if doc:
            new_form_workflow(doc, SENDER_CLINIC, patient_id)
        return HttpResponseRedirect(reverse("single_patient", args=(patient_id,)))  

    patient = CPatient.get(patient_id)

    xform = encounter_info.get_xform()
    # TODO: generalize this better
    preloader_tags = {"case": {"patient_id" : patient_id,
                               "age_years" : str(patient.age) if patient.age != None else '',
                               "dob": patient.birthdate.strftime('%Y-%m-%d') if patient.birthdate else '',
                               "gender" : patient.gender,
                               "bhoma_case_id" : "<uid>",
                               "case_id" : "<uid>"},
                      "meta": {"clinic_id": settings.BHOMA_CLINIC_ID,
                               "user_id":   request.user.get_profile()._id,
                               "username":  request.user.username}}
                               
    return xforms_views.play(request, xform.id, callback, preloader_tags)

@restricted_patient_data
@permission_required("webapp.bhoma_enter_data")
def patient_select(request):
    """
    Entry point for patient select/registration workflow
    """
    if request.method == "POST":
        data = json.loads(request.POST.get('result'))
        merge_id = data.get("merge_with", None) 
        create_new = data.get("new") and not merge_id 
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
                    new_dict[newkey] = pat_dict.get(oldkey)
                return new_dict
            clean_data = map_basic_data(pat_dict)
            patient = patient_from_instance(clean_data)
            if pat_dict.get("phone"):
                patient.phones=[CPhone(is_default=True, number=pat_dict["phone"])]
            else:
                patient.phones = []
            
            # TODO: create an encounter for this reg?
            patient.address = CAddress(village=pat_dict.get("village"), 
                                       clinic_id=settings.BHOMA_CLINIC_ID,
                                       zone=pat_dict.get("chw_zone"),
                                       zone_empty_reason=pat_dict.get("chw_zone_na"))
            patient.clinic_ids = [settings.BHOMA_CLINIC_ID,]
            
            patient.save()
            return HttpResponseRedirect(reverse("single_patient", args=(patient.get_id,)))
        elif merge_id:
            return HttpResponseRedirect(reverse("single_patient", args=(merge_id,)))
        elif pat_dict is not None:
            # we get a real couch patient object in this case
            pat_uid = pat_dict["_id"]
            return HttpResponseRedirect(reverse("single_patient", args=(pat_uid,)))
        
    return render_to_response(request, "bhoma_touchscreen.html", 
                              {'form': {'name': 'patient reg', 
                                        'wfobj': 'wfGetPatient'}, 
                               'mode': 'workflow',
                               'dynamic_scripts': ["patient/javascripts/patient_reg.js",] })
    
@restricted_patient_data
def render_content (request, template):
    if template == 'single-patient':
        pat_uuid = request.POST.get('uuid')
        if pat_uuid:
            patient = loader.get_patient(pat_uuid)
            return render_to_response(request, 'patient/single_patient_block.html', {'patient': patient})
        else: 
            return HttpResponse("No patient.")
    elif template == 'single-patient-edit':
        patient = json.loads(request.raw_post_data)
        patient['dob'] = string_to_datetime(patient['dob']).date() if patient['dob'] else None
        return render_to_response(request, 'patient/patient_edit_overview.html', {'patient': patient})
    else:
        return HttpResponse(("Unknown template type: %s. What are you trying " 
                             "to do and how did you get here?") % template)

@restricted_patient_data
def patient_case(request, patient_id, case_id):
    pat = CPatient.get(patient_id)
    found_case = None
    for case in pat.cases:
        if case.get_id == case_id:
            found_case = case
            break
    return render_to_response(request, "case/single_case.html", 
                              {"patient": pat,
                               "case": found_case,
                               "options": TouchscreenOptions.default()})
    
# import our api views so they can be referenced normally by django.
# this is just a code cleanliness issue
from api_views import *
