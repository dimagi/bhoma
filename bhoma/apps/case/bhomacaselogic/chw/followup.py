from bhoma.apps.case.xform import extract_case_blocks
from bhoma.apps.case import const
from dimagi.utils.couch.database import get_db
from bhoma.apps.case.models.couch import PatientCase, CommCareCaseAction
from datetime import datetime, time
import logging
from bhoma.apps.case.bhomacaselogic.shared import get_commcare_case_id_from_block,\
    get_commcare_case_name, new_commcare_case, get_user_id,\
    add_missed_appt_dates
from dimagi.utils.parsing import string_to_datetime
from couchdbkit.exceptions import MultipleResultsFound
from bhoma.apps.patient.encounters import config

is_delivery = lambda bhoma_case: bhoma_case.type == const.CASE_TYPE_DELIVERY

def process_followup(patient, new_encounter):
    form = new_encounter.get_xform()
    assert form.namespace == config.CHW_FOLLOWUP_NAMESPACE
    caseblocks = extract_case_blocks(form)
    for caseblock in caseblocks:
        case_id = caseblock[const.CASE_TAG_ID]
        # find bhoma case 
        try:
            results = get_db().view("case/bhoma_case_lookup", key=case_id, reduce=False).one()
        except MultipleResultsFound:
            logging.error("Found duplicate cases in a patient: patient_id: %s, case_id: %s" % (patient.get_id, case_id))
            results = None
        if results:
            raw_data = results["value"]
            bhoma_case = PatientCase.wrap(raw_data)
            for case in bhoma_case.commcare_cases:
                if case.case_id == case_id:
                    # apply generic commcare update to the case
                    case.update_from_block(caseblock, new_encounter.visit_date)
                    
                    # apply custom updates to bhoma case
                    bhoma_case_close_value = case.all_properties().get(const.CASE_TAG_BHOMA_CLOSE, None)
                    bhoma_case_outcome_value = case.all_properties().get(const.CASE_TAG_BHOMA_OUTCOME, "")
                            
                    if bhoma_case_close_value and int(bhoma_case_close_value):
                        # bhoma case should be closed
                        if bhoma_case.closed:
                            logging.warn("Tried to close case %s from phone but it was already closed! Ignoring." % bhoma_case.get_id) 
                        else:
                            bhoma_case.closed = True
                            bhoma_case.outcome = bhoma_case_outcome_value
                            bhoma_case.closed_on = datetime.combine(new_encounter.visit_date, time())
                    else:
                        # we didn't close the bhoma case, check if we need to 
                        # create any new commcare cases

                        # referred back: create an appointment
                        if bhoma_case_outcome_value == const.Outcome.REFERRED_BACK_TO_CLINIC:
                            appt_date_string = form.xpath("met/followup/refer_when")
                            if appt_date_string:
                                new_case = new_commcare_case(case_id=get_commcare_case_id_from_block(new_encounter, bhoma_case),
                                                             name=get_commcare_case_name(new_encounter, bhoma_case), 
                                                             type=bhoma_case.type, 
                                                             opened_on=datetime.combine(new_encounter.visit_date, time()), 
                                                             modified_on=datetime.utcnow(),
                                                             user_id=get_user_id(new_encounter), 
                                                             encounter_id=new_encounter.get_id, 
                                                             bhoma_case_id=bhoma_case.get_id)
                                new_case.followup_type = const.PHONE_FOLLOWUP_TYPE_MISSED_APPT
                                appt_date = string_to_datetime(appt_date_string).date()
                                add_missed_appt_dates(new_case, appt_date)
                                bhoma_case.status = const.Status.RETURN_TO_CLINIC
                                bhoma_case.commcare_cases.append(new_case)
                        elif bhoma_case_outcome_value == const.Outcome.ACTUALLY_WENT_TO_CLINIC:
                            bhoma_case.status = const.STATUS_WENT_BACK_TO_CLINIC
                        elif bhoma_case_outcome_value == const.Outcome.PENDING_PATIENT_MEETING:
                            bhoma_case.status = const.STATUS_PENDING_CHW_MEETING

            if is_delivery(bhoma_case):
                custom_process_delivery_case(bhoma_case, new_encounter)

            patient.update_cases([bhoma_case])
        else:
            logging.error(("No case in patient %s with id %s found.  "
                           "If you are not debugging then this is a weird error.") % (patient.get_id, case_id))

def custom_process_delivery_case(bhoma_case, encounter):
    form = encounter.get_xform()
    # baby_alive = form.xpath('met/followup/postnatal/baby_alive')
    # if baby_alive:
    #     bhoma_case.baby_alive = baby_alive
    #     if baby_alive == 'n':
    #         bhoma_case.baby_cause_of_death = form.xpath('met/followup/postnatal/infant_death/cause_of_death')
    # if bhoma_case.outcome == 'died':
    #     bhoma_case.mother_alive = 'n'
    #     bhoma_case.mother_cause_of_death = form.xpath('no_meet/postnatal_death/cause_of_death')

    if bhoma_case.closed:
        max_mod_date = max(*[c.modified_on for c in bhoma_case.commcare_cases])
        for subcase in bhoma_case.commcare_cases:
            if not subcase.closed:
                close_action = CommCareCaseAction(
                    action_type=const.CASE_ACTION_CLOSE,
                    date=max_mod_date or datetime.utcnow(),
                    visit_date=encounter.visit_date,
                )
                subcase.apply_close(close_action)
