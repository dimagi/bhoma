from bhoma.utils.render_to_response import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from bhoma.apps.encounter.forms import EncounterForm
from bhoma.apps.patient.models import CPatient


def encounters_for_patient(request, patient_id):
    render_to_response(request, "", {})
    
    
def new_encounter(request, patient_id):
    
    encounter = None
    patient = CPatient.view("patient/all", key=patient_id).one()
    
    if request.POST:
        form = EncounterForm(request.POST)
        if form.is_valid():
            encounter = form.save(commit=False)
            encounter.patient = patient
            encounter.save()
            return HttpResponseRedirect(reverse("single_patient", args=[patient_id]))  
    else:
        form = EncounterForm()
        
    return render_to_response(request, "encounter/new_encounter.html", 
                              {"form": form,
                               "encounter": encounter})
                                

    