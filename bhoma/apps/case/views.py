from bhoma.utils.couch.database import get_db
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from bhoma.apps.case.models.couch import PatientCase

def duplicates(request):
    all_cases = get_db().view("case/counts_by_id", reduce=True, group=True)
    duplicate_cases = {}
    for row in all_cases:
        if int(row["value"]) > 1:
            duplicate_cases[row["key"]] = row["value"]
            
    return render_to_response('case/duplicates.html',
                              {"cases" : duplicate_cases},
                               context_instance=RequestContext(request))
    
def duplicate_details(request, case_id):
    case_details = PatientCase.view("case/all_and_patient", key=case_id)
    return render_to_response('case/details.html',
                              {"case_id": case_id, 
                               "cases" : case_details},
                               context_instance=RequestContext(request))
    
