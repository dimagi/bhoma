from bhoma.utils.render_to_response import render_to_response
from django.http import HttpResponse
from django_digest.decorators import *
from django.core.urlresolvers import reverse

@httpdigest
def test(request):
    """
    Test view
    """
    return HttpResponse(TESTING_RESTORE_DATA)

TESTING_RESTORE_DATA=\
"""<restoredata> 
<n0:registration xmlns:n0="http://openrosa.org/user-registration"><username>bhoma</username><password>bhoma</password><uuid>O9KNJQO8V951GSOXDV7604I1Q</uuid><date>2010-07-28</date><registering_phone_id>SSNCFBLR8U12WB3I8RMKRTACC</registering_phone_id><user_data><data key="providertype">hbcp</data><data key="training">yes</data><data key="sex">m</data><data key="user_type">standard</data></user_data></n0:registration><case> 
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