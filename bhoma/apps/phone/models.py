from datetime import datetime
from couchdbkit.ext.django.schema import *
import logging
from bhoma.apps.case import const
from bhoma.apps.phone import phonehacks
from bhoma.utils.couch import safe_index
import sha
import hashlib
from bhoma.utils.mixins import UnicodeMixIn

class SyncLog(Document, UnicodeMixIn):
    """
    A log of a single sync operation.
    """
    
    date = DateTimeProperty()
    chw_id = StringProperty()
    previous_log_id = StringProperty() # previous sync log, forming a chain
    last_seq = IntegerProperty() # the last_seq of couch during this sync
    cases = StringListProperty()
    
    def get_previous_log(self):
        """
        Get the previous sync log, if there was one.  Otherwise returns nothing.
        """
        if self.previous_log_id:
            return SyncLog.get(self.previous_log_id)
        return None
    
    def get_synced_case_ids(self):
        """
        All cases that have been touched, either by this or
        any previous syncs that this knew about.
        """
        if not hasattr(self, "_touched_case_ids"):
            cases = [case for case in self.cases]
            previous_log = self.get_previous_log()
            if previous_log:
                cases.extend(previous_log.get_synced_case_ids())
            # remove duplicates
            self._touched_case_ids = list(set(cases))
        return self._touched_case_ids
    
    def __unicode__(self):
        return "%s of %s on %s (%s)" % (self.operation, self.chw_id, self.date.date(), self._id)

class PhoneCase(Document, UnicodeMixIn):
    """
    Case objects that go to phones.  These are a bizarre, nasty hacked up 
    agglomeration of bhoma (patient) and commcare cases.
    """
    
    case_id = StringProperty()
    date_modified = DateTimeProperty()
    case_type_id = StringProperty()
    user_id = StringProperty()
    case_name = StringProperty()
    external_id = StringProperty()
    
    # patient data 
    patient_id = StringProperty()
    patient_rev = StringProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    birth_date = DateProperty()
    birth_date_est = BooleanProperty()
    age = StringProperty()
    sex = StringProperty()
    village = StringProperty()
    contact = StringProperty()
    
    # bhoma properties
    bhoma_case_id = StringProperty()
    bhoma_patient_id = StringProperty()
    followup_type = StringProperty()
    orig_visit_type = StringProperty()
    orig_visit_diagnosis = StringProperty()
    orig_visit_date = DateProperty()
    activation_date = DateProperty() # (don't followup before this date) 
    due_date = DateProperty() # (followup by this date)
    missed_appt_date = DateProperty()
    
    def __unicode__(self):
        return self.get_unique_string()
    
    def get_unique_string(self):
        """
        A unique identifier for this based on some of its contents
        """
        # in theory since case ids are unique and modification dates get updated
        # upon any change, this is all we need
        return "%(case_id)s::%(date_modified)s::%(patient_id)s::%(patient_rev)s" % \
                {"case_id": self.case_id, "date_modified": self.date_modified,
                 "patient_id": self.patient_id, "patient_rev": self.patient_rev}
    
    def _get_id(self):
        return hashlib.sha1(self.get_unique_string()).hexdigest()
        
    def save(self, *args, **kwargs):
        # override save to make this read-only, use a generated id,
        # and not re-save objects that have already been saved
        if self._id:
            raise Exception("Sorry this model is read only and the ID must be "
                            "automatically generated!")
        
        id = self._get_id()
        if PhoneCase.get_db().doc_exist(id):
            # we assume we don't need to recreate this, since it's the same
            # exact object
            pass
        else:
            self._id = id
            super(PhoneCase, self).save(*args, **kwargs)
    
    
    @classmethod
    def from_bhoma_case(cls, case):
        if not case.patient:
            logging.error("No patient found found inside %s, will not be downloaded to phone" % case)
            return None
        
        # complicated logic, but basically a case is open based on the conditions 
        # below which amount to it not being closed, and if it has a start date, 
        # that start date being before or up to today
        open_inner_cases = [cinner for cinner in case.commcare_cases \
                            if not cinner.closed and cinner.is_started()]
                               
        if len(open_inner_cases) == 0:
            logging.warning("No open case found inside %s, will not be downloaded to phone" % case)
            return None
        elif len(open_inner_cases) > 1:
            logging.error("More than one open case found inside %s.  Only the most recent will not be downloaded to phone" % case)
            ccase = sorted(open_inner_cases, key=lambda case: case.opened_on)[0]
        else:
            ccase = open_inner_cases[0]
        
        missed_appt_date = safe_index(ccase, ["missed_appointment_date",])
        if missed_appt_date:
            # if it's there it's a datetime, force it to a date 
            missed_appt_date = missed_appt_date.date()
        return PhoneCase(**{"case_id": ccase._id,
                            "date_modified": case.modified_on,
                            "case_type_id": const.CASE_TYPE_BHOMA_FOLLOWUP,
                            "user_id": ccase.user_id,
                            "case_name": ccase.name,
                            "external_id": ccase.external_id,
                            "patient_id": case.patient.get_id,
                            "patient_rev": case.patient.get_rev,
                            "first_name": case.patient.first_name,
                            "last_name": case.patient.last_name,
                            "birth_date": case.patient.birthdate,
                            "birth_date_est": case.patient.birthdate_estimated, 
                            "age": case.patient.formatted_age, 
                            "sex": case.patient.gender,
                            "village": case.patient.address.village,
                            "contact": case.patient.default_phone,
                            "bhoma_case_id": case.get_id, # TODO: remove? duplicate with external_id
                            "bhoma_patient_id": case.patient.get_id, 
                            
                            "followup_type": phonehacks.followup_type_transform(ccase.followup_type), # (post-hospital, missed appt, chw followup, etc.)
                            "orig_visit_type": phonehacks.original_visit_type_transform(case.get_encounter().type), # (general, under-5, etc.)
                            "orig_visit_diagnosis": case.type,
                            "orig_visit_date": case.get_encounter().visit_date,
                            "activation_date": ccase.activation_date, 
                            "due_date": ccase.due_date, 
                            
                            "missed_appt_date": missed_appt_date
                            })
