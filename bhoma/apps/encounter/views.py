from dimagi.utils.web import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from bhoma.apps.encounter.forms import EncounterForm
from bhoma.apps.patient.models import CPatient
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions
from bhoma.apps.patient import loader


def encounters_for_patient(request, patient_id):
    render_to_response(request, "", {})
    

def single_encounter(request, patient_id, encounter_id):
    patient = loader.get_patient(patient_id)
    encounters = [enc for enc in patient.encounters if enc.get_id == encounter_id]
    if not encounters:
        raise Exception("No matching encounter for id %s in patient %s" % (encounter_id, patient_id))
    encounter = encounters[0]
    return render_to_response(request, "encounter/single_encounter.html", 
                              {"patient": patient,
                               "encounter": encounter,
                               "options": TouchscreenOptions.default()})