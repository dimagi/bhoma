from bhoma.utils.render_to_response import render_to_response
from django.http import HttpResponse
from django_digest.decorators import *
from django.core.urlresolvers import reverse
from bhoma.apps.chw.models import CommunityHealthWorker
from bhoma.apps.phone import xml
from bhoma.apps.phone.models import SyncLog
from django.views.decorators.http import require_POST
from bhoma.apps.case.models.couch import PatientCase
import bhoma.apps.xforms.views as xforms_views
from bhoma.apps.patient.encounters import config
from bhoma.apps.case.xform import extract_case_blocks
from bhoma.apps.case import const
from bhoma.apps.xforms import const as xforms_const
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.phone.caselogic import meets_sending_criteria, cases_for_chw

@httpdigest
def restore(request) :
    
    restore_id_from_request = lambda req: req.GET.get("since")
    restore_id = restore_id_from_request(request)
    last_sync = None
    if restore_id:
        # TODO: figure out what to do about this
        last_sync = SyncLog.objects.get(_id=restore_id)
    
    username = request.user.username
    chw_id = request.user.get_profile().chw_id
    if not chw_id:
        raise Exception("No linked chw found for %s" % username)
    chw = CommunityHealthWorker.view("chw/all", key=chw_id).one()
    
    all_cases = cases_for_chw(chw)
    
    # filter out those which should not be sent
    cases_to_send = [case for case in all_cases if meets_sending_criteria(case, last_sync)]
    case_xml_blocks = [xml.get_case_xml(case) for case in cases_to_send]
    # create a sync log for this
    if last_sync == None:
        reg_xml = xml.get_registration_xml(chw)
        synclog = SyncLog.objects.create(operation="ir", chw_id=chw_id)
    else:
        reg_xml = "" # don't sync registration after initial sync
        synclog = SyncLog.objects.create(operation="cu", chw_id=chw_id)
    to_return = xml.RESTOREDATA_TEMPLATE % {"registration": reg_xml, 
                                            "restore_id": synclog._id, 
                                            "case_list": "".join(case_xml_blocks)}
    return HttpResponse(to_return, mimetype="text/xml")
    
@require_POST
def post(request):
    """
    Post an xform instance here.
    """
    def callback(doc):
        # TODO: post process
        # check xmlns
        is_followup = doc[xforms_const.TAG_NAMESPACE] == config.CHW_FOLLOWUP_NAMESPACE 
        if is_followup:
            caseblocks = extract_case_blocks(doc)
            for caseblock in caseblocks:
                case_id = caseblock[const.CASE_TAG_ID]
                # find bhoma case 
                results = get_db().view("case/bhoma_case_lookup", key=case_id).one()
                pat_id = results["id"]
                raw_data = results["value"]
                patient = CPatient.get(pat_id)
                bhoma_case = PatientCase.wrap(raw_data)
                # bhoma_case = PatientCase.view_with_patient("case/bhoma_case_lookup", key=case_id).one()
                for case in bhoma_case.commcare_cases:
                    if case.case_id == case_id:
                        # apply updates
                        case.update_from_block(caseblock)
                        # apply custom updates to bhoma case
                        if case.all_properties().get(const.CASE_TAG_BHOMA_CLOSE, None):
                            bhoma_case.closed = True
                            bhoma_case.outcome = case.all_properties().get(const.CASE_TAG_BHOMA_OUTCOME, "")
                            bhoma_case.closed_on = case.modified_on
                # save
                patient.update_cases([bhoma_case,])
                patient.save()
        
        return HttpResponse("It works!")

    return xforms_views.post(request, callback)


@httpdigest
def test(request):
    """
    Test view
    """
    return HttpResponse(TESTING_RESTORE_DATA, mimetype="text/xml")


TESTING_RESTORE_DATA=\
"""<restoredata> 
<n0:registration xmlns:n0="http://openrosa.org/user-registration">
  <username>bhoma</username>
  <password>234</password>
  <uuid>O9KNJQO8V951GSOXDV7604I1Q</uuid>
  <date>2010-07-28</date>
  <registering_phone_id>SSNCFBLR8U12WB3I8RMKRTACC</registering_phone_id>
  <user_data>
    <data key="providertype">hbcp</data>
    <data key="training">yes</data>
    <data key="sex">m</data>
    <data key="user_type">standard</data>
  </user_data>
</n0:registration>
<case>
<case_id>PZHBCC9647XX0V4YAZ2UUPQ9M</case_id>
<date_modified>2010-07-28T14:49:57.930</date_modified>
<create>
  <case_type_id>bhoma_followup</case_type_id>
  <user_id>O9KNJQO8V951GSOXDV7604I1Q</user_id>
  <case_name>6</case_name>
  <external_id>bhoma8972837492818239</external_id>
</create>
<update>
  <first_name>DREW</first_name>
  <last_name>ROOS</last_name>
  <birth_date>1983-10-06</birth_date>
  <birth_date_est>1</birth_date_est>
  <age>26</age>
  <sex>m</sex>
  <village>SOMERVILLE</village>
  <contact>9183739767</contact>

  <followup_type>missed_appt</followup_type>
  <orig_visit_type>general</orig_visit_type>
  <orig_visit_diagnosis>malaria</orig_visit_diagnosis>
  <orig_visit_date>2010-07-12</orig_visit_date>

  <activation_date>2010-07-27</activation_date>
  <due_date>2010-07-31</due_date>

  <missed_appt_date>2010-07-24</missed_appt_date>
  <ttl_missed_appts>1</ttl_missed_appts>
</update>
</case>

<case>
<case_id>UJ3IN4HBLNTBRNV2SVCE6F5VU</case_id>
<date_modified>2010-07-28T14:49:57.930</date_modified>
<create>
  <case_type_id>bhoma_followup</case_type_id>
  <user_id>O9KNJQO8V951GSOXDV7604I1Q</user_id>
  <case_name>7</case_name>
  <external_id>bhoma20938968738923</external_id>
</create>
<update>
  <first_name>LESTER</first_name>
  <last_name>JENKINS</last_name>
  <birth_date>1934-02-23</birth_date>
  <birth_date_est>0</birth_date_est>
  <age>76</age>
  <sex>m</sex>
  <village>DORCHESTER</village>
  <contact>7814359283</contact>

  <followup_type>hospital</followup_type>
  <orig_visit_type>general</orig_visit_type>
  <orig_visit_diagnosis>pneumonia</orig_visit_diagnosis>
  <orig_visit_date>2010-07-24</orig_visit_date>

  <activation_date>2010-08-03</activation_date>
  <due_date>2010-08-07</due_date>
</update>
</case>

<case>
<case_id>MYTF9AFKZPX8TGYOAXXLUEKCE</case_id>
<date_modified>2010-07-28T14:49:57.930</date_modified>
<create>
  <case_type_id>bhoma_followup</case_type_id>
  <user_id>O9KNJQO8V951GSOXDV7604I1Q</user_id>
  <case_name>8</case_name>
  <external_id>bhoma9989500849805480848</external_id>
</create>
<update>
  <first_name>HEZRAH</first_name>
  <last_name>D'MAGI</last_name>
  <birth_date>2007-11-01</birth_date>
  <birth_date_est>0</birth_date_est>
  <age>2</age>
  <sex>f</sex>
  <village>CHARLESTOWN</village>
  <contact></contact>

  <followup_type>chw_followup</followup_type>
  <orig_visit_type>under_five</orig_visit_type>
  <orig_visit_diagnosis>diarrhea</orig_visit_diagnosis>
  <orig_visit_date>2010-07-31</orig_visit_date>

  <activation_date>2010-08-03</activation_date>
  <due_date>2010-08-07</due_date>
</update>
</case>


</restoredata>
"""
