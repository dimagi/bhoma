from bhoma.utils.render_to_response import render_to_response
from django.http import HttpResponse
from django_digest.decorators import *
from django.core.urlresolvers import reverse
from bhoma.apps.chw.models import CommunityHealthWorker
from bhoma.apps.phone import xml
from bhoma.apps.phone.models import SyncLog
from django.views.decorators.http import require_POST
from bhoma.apps.case.models.couch import PatientCase

@httpdigest
def restore(request):
    """
    Restore a CHW object from a phone.
    """
    username = request.user.username
    chw_id = request.user.get_profile().chw_id
    if not chw_id:
        raise Exception("No linked chw found for %s" % username)
    chw = CommunityHealthWorker.view("chw/all", key=chw_id).one()
    reg_xml = xml.get_registration_xml(chw)
    to_return = xml.RESTOREDATA_TEMPLATE % {"inner": reg_xml}
    # create a sync log for this
    SyncLog.objects.create(operation="ir", chw_id=chw_id)
    return HttpResponse(to_return, mimetype="text/xml")

@httpdigest
def case_list(request):
    username = request.user.username
    chw_id = request.user.get_profile().chw_id
    if not chw_id:
        raise Exception("No linked chw found for %s" % username)
    chw = CommunityHealthWorker.view("chw/all", key=chw_id).one()
    
    # from chw clinic zone, get the list of open cases
    key = [chw.current_clinic_id, chw.current_clinic_zone]
    all_cases = PatientCase.view_with_patient("case/open_for_chw", key=key).all()
    
    # filter out those which should not be sent
    cases_to_send = [case for case in all_cases if case.meets_sending_criteria()]
            
    for case in cases_to_send:
        case_xml = xml.get_case_xml(case)
        
    reg_xml = xml.get_registration_xml(chw)
    to_return = xml.RESTOREDATA_TEMPLATE % {"inner": reg_xml}
    # create a sync log for this
    SyncLog.objects.create(operation="ir", chw_id=chw_id)
    return HttpResponse(to_return, mimetype="text/xml")
    
@require_POST
def post(request):
    """
    Post an xform instance here.
    """
    pass

@httpdigest
def test(request):
    """
    Test view
    """
    return HttpResponse(TESTING_RESTORE_DATA, mimetype="text/xml")


TESTING_RESTORE_DATA=\
"""<restoredata> 
<n0:registration xmlns:n0="http://openrosa.org/user-registration"><username>bhoma</username><password>bhoma</password><uuid>O9KNJQO8V951GSOXDV7604I1Q</uuid><date>2010-07-28</date><registering_phone_id>SSNCFBLR8U12WB3I8RMKRTACC</registering_phone_id><user_data><data key="providertype">hbcp</data><data key="training">yes</data><data key="sex">m</data><data key="user_type">standard</data></user_data></n0:registration>
<case>
    <case_id> 
        PZHBCC9647XX0V4YAZ2UUPQ9M
    </case_id> 
    <date_modified> 
        2010-07-28T14:49:57.930
    </date_modified> 
    <create> 
        <case_type_id> 
            cc_pf_client
        </case_type_id> 
        <user_id> 
            O9KNJQO8V951GSOXDV7604I1Q
        </user_id> 
        <case_name> 
            PM-SONGEA
        </case_name> 
        <external_id> 
            .
        </external_id> 
    </create> 
    <update> 
        <pat_inits> 
            PM
        </pat_inits> 
        <sex> 
            m
        </sex> 
        <dob> 
            1970-07-28
        </dob> 
        <village> 
            SONGEA
        </village> 
    </update> 
</case> 
</restoredata>
"""