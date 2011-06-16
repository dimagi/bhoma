from __future__ import absolute_import
from datetime import datetime, date, time, timedelta
from couchdbkit.ext.django.schema import *
from bhoma.apps.case import const
from dimagi.utils import parsing
from couchdbkit.schema.properties_proxy import SchemaListProperty
import logging
from bhoma.apps.patient.mixins import PatientQueryMixin
from bhoma.apps.xforms.util import value_for_display
from bhoma.apps.encounter.models.couch import Encounter
from dimagi.utils.mixins import UnicodeMixIn
from bhoma.apps.case.bhomacaselogic.pregnancy.calc import lmp_from_edd, get_edd
    
from bhoma.apps.case.bhomacaselogic.pregnancy.pregnancy import DAYS_BEFORE_LMP_START,\
    DAYS_AFTER_EDD_END
from bhoma.apps.xforms.models.couch import CXFormInstance
from bhoma.apps.case.bhomacaselogic.followups import get_pregnancy_followup

"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.

For details on casexml check out:
http://bitbucket.org/javarosa/javarosa/wiki/casexml
"""

class CaseBase(Document, UnicodeMixIn):
    """
    Base class for cases and referrals.
    """
    opened_on = DateTimeProperty()
    modified_on = DateTimeProperty()
    closed_on = DateTimeProperty()
    
    # the primary diagnosis - the purpose of this case 
    type = StringProperty()
    
    closed = BooleanProperty(default=False)
    # when a case is closed automatically or by a chw, we use this to 
    # track whether it's been recorded into the paper system.
    # TODO: (re)move this?
    recorded = BooleanProperty(default=False) 
    
    
    class Meta:
        app_label = 'case'

    def __unicode__(self):
        return "id: %(id)s, type: %(type)s, opened on: %(opened)s, closed: %(closed)s" %  \
                {"id": self.get_id, "opened": self.opened_on, "closed": self.closed,
                 "type": self.type }

class CommCareCaseAction(Document):
    """
    An atomic action on a case. Either a create, update, or close block in
    the xml.  
    """
    
    action_type = StringProperty()
    date = DateTimeProperty()
    visit_date = DateProperty()
    
    @classmethod
    def from_action_block(cls, action, date, visit_date, action_block):
        if not action in const.CASE_ACTIONS:
            raise ValueError("%s not a valid case action!")
        
        action = CommCareCaseAction(action_type=action, date=date, visit_date=visit_date)
        
        # a close block can come without anything inside.  
        # if this is the case don't bother trying to post 
        # process anything
        if isinstance(action_block, basestring):
            return action
            
        action.type = action_block.get(const.CASE_TAG_TYPE_ID)
        action.name = action_block.get(const.CASE_TAG_NAME)
        if const.CASE_TAG_DATE_OPENED in action_block:
            action.opened_on = parsing.string_to_datetime(action_block[const.CASE_TAG_DATE_OPENED])
        
        for item in action_block:
            if item not in const.CASE_TAGS:
                action[item] = action_block[item]
        return action
    
    @classmethod
    def new_create_action(cls, date=None):
        """
        Get a new create action
        """
        if not date: date = datetime.utcnow()
        return CommCareCaseAction(action_type=const.CASE_ACTION_CLOSE, 
                                  date=date, visit_date=date.date(), 
                                  opened_on=date)
    
    @classmethod
    def new_close_action(cls, date=None):
        """
        Get a new close action
        """
        if not date: date = datetime.utcnow()
        return CommCareCaseAction(action_type=const.CASE_ACTION_CLOSE, 
                                  date=date, visit_date=date.date(),
                                  closed_on=date)
    
    class Meta:
        app_label = 'case'

    
class CReferral(CaseBase):
    """
    A referral, taken from casexml.  
    """
    
    
    # Referrals have top-level couch guids, but this id is important
    # to the phone, so we keep it here.  This is _not_ globally unique
    # but case_id/referral_id/type should be.  
    # (in our world: case_id/referral_id/type)
    referral_id = StringProperty()
    followup_on = DateTimeProperty()
    outcome = StringProperty()
    
    class Meta:
        app_label = 'case'

    def __unicode__(self):
        return ("%s:%s" % (self.type, self.referral_id))
        
    def apply_updates(self, date, referral_block):
        if not const.REFERRAL_ACTION_UPDATE in referral_block:
            logging.warn("No update action found in referral block, nothing to be applied")
            return
        
        update_block = referral_block[const.REFERRAL_ACTION_UPDATE] 
        if not self.type == update_block[const.REFERRAL_TAG_TYPE]:
            raise logging.warn("Tried to update from a block with a mismatched type!")
            return
        
        if date > self.modified_on:
            self.modified_on = date
        
        if const.REFERRAL_TAG_FOLLOWUP_DATE in referral_block:
            self.followup_on = parsing.string_to_datetime(referral_block[const.REFERRAL_TAG_FOLLOWUP_DATE])
        
        if const.REFERRAL_TAG_DATE_CLOSED in update_block:
            self.closed = True
            self.closed_on = parsing.string_to_datetime(update_block[const.REFERRAL_TAG_DATE_CLOSED])
            
            
    @classmethod
    def from_block(cls, date, block):
        """
        Create referrals from a block of processed data (a dictionary)
        """
        if not const.REFERRAL_ACTION_OPEN in block:
            raise ValueError("No open tag found in referral block!")
        id = block[const.REFERRAL_TAG_ID]
        follow_date = parsing.string_to_datetime(block[const.REFERRAL_TAG_FOLLOWUP_DATE])
        open_block = block[const.REFERRAL_ACTION_OPEN]
        types = open_block[const.REFERRAL_TAG_TYPES].split(" ")
        
        ref_list = []
        for type in types:
            ref = CReferral(referral_id=id, followup_on=follow_date, 
                            type=type, opened_on=date, modified_on=date, 
                            closed=False)
            ref_list.append(ref)
        
        # there could be a single update block that closes a referral
        # that we just opened.  not sure why this would happen, but 
        # we'll support it.
        if const.REFERRAL_ACTION_UPDATE in block:
            update_block = block[const.REFERRAL_ACTION_UPDATE]
            for ref in ref_list:
                if ref.type == update_block[const.REFERRAL_TAG_TYPE]:
                    ref.apply_updates(date, block)
        
        return ref_list

class CommCareCase(CaseBase, PatientQueryMixin):
    """
    A case, taken from casexml.  This represents the latest
    representation of the case - the result of playing all
    the actions in sequence.  These cases are the ones that
    are sent to phones, and are normal commcare cases.
    """
    external_id = StringProperty()
    encounter_id = StringProperty()
    referrals = SchemaListProperty(CReferral)
    actions = SchemaListProperty(CommCareCaseAction)
    name = StringProperty()
    
    # this field is sent to the phone and represents one of a few possibilities
    # either the patient missed an appointment at the clinic, is being checked
    # up on after they were referred to the hospital
    followup_type = StringProperty()
    
    # date the case actually starts, before this won't be sent to phone.
    # this is for missed appointments, which don't start until the appointment
    # is actually missed
    start_date = DateProperty()      
    activation_date = DateProperty() # date the phone triggers it active
    due_date = DateProperty()        # date the phone thinks it's due
    missed_appointment_date = DateProperty()   # date of a missed appointment, if any
    
    
    class Meta:
        app_label = 'case'
    
    def __unicode__(self):
        try:
            return "%s, due: %s" % (super(CommCareCase, self).__unicode__(), self.due_date)
        except Exception, e:
            return str(e)
    
    def _get_case_id(self):
        return self._id
    
    def _set_case_id(self, value):
        if getattr(self, "_id", None) is not None and self._id != value:
            raise Exception("can't change case id once it has been set!")
        self._id = value
    
    def get_version_token(self):
        """
        A unique token for this version. 
        """
        # in theory since case ids are unique and modification dates get updated
        # upon any change, this is all we need
        return "%(case_id)s::%(date_modified)s" % (self.case_id, self.date_modified)
    
    case_id = property(_get_case_id, _set_case_id)
    
    def is_started(self, since=None):
        """
        Whether the case has started (since a date, or today).
        """
        if since is None:
            since = date.today()
        return self.start_date <= since if self.start_date else True
    
    @classmethod
    def from_doc(cls, case_block):
        """
        Create a case object from a case block.
        """
        if not const.CASE_ACTION_CREATE in case_block:
            raise ValueError("No create tag found in case block!")
        
        # create case from required fields in the case/create block
        create_block = case_block[const.CASE_ACTION_CREATE]
        id = case_block[const.CASE_TAG_ID]
        opened_on = parsing.string_to_datetime(case_block[const.CASE_TAG_MODIFIED])
        
        # create block
        type = create_block[const.CASE_TAG_TYPE_ID]
        name = create_block[const.CASE_TAG_NAME]
        external_id = create_block[const.CASE_TAG_EXTERNAL_ID]
        user_id = create_block[const.CASE_TAG_USER_ID] if const.CASE_TAG_USER_ID in create_block else ""
        create_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_CREATE, 
                                                             opened_on, opened_on.date(),
                                                             create_block)
        
        case = CommCareCase(case_id=id, opened_on=opened_on, modified_on=opened_on, 
                     type=type, name=name, user_id=user_id, external_id=external_id, 
                     closed=False, actions=[create_action,])
        
        # apply initial updates, referrals and such, if present
        case.update_from_block(case_block)
        return case
    
    def update_from_block(self, case_block, visit_date=None):
        
        mod_date = parsing.string_to_datetime(case_block[const.CASE_TAG_MODIFIED])
        if mod_date > self.modified_on:
            self.modified_on = mod_date
        
        # you can pass in a visit date, to override the udpate/close action dates
        if not visit_date:
            visit_date = mod_date.date()
        
        
        if const.CASE_ACTION_UPDATE in case_block:
            update_block = case_block[const.CASE_ACTION_UPDATE]
            update_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_UPDATE, 
                                                                 mod_date, visit_date, 
                                                                 update_block)
            self.apply_updates(update_action)
            self.actions.append(update_action)
        
        if const.CASE_ACTION_CLOSE in case_block:
            close_block = case_block[const.CASE_ACTION_CLOSE]
            close_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_CLOSE, 
                                                                mod_date, visit_date, 
                                                                close_block)
            self.apply_close(close_action)
            
        if const.REFERRAL_TAG in case_block:
            referral_block = case_block[const.REFERRAL_TAG]
            if const.REFERRAL_ACTION_OPEN in referral_block:
                referrals = CReferral.from_block(mod_date, referral_block)
                # for some reason extend doesn't work.  disconcerting
                # self.referrals.extend(referrals)
                for referral in referrals:
                    self.referrals.append(referral)
            elif const.REFERRAL_ACTION_UPDATE in referral_block:
                found = False
                update_block = referral_block[const.REFERRAL_ACTION_UPDATE]
                for ref in self.referrals:
                    if ref.type == update_block[const.REFERRAL_TAG_TYPE]:
                        ref.apply_updates(mod_date, referral_block)
                        found = True
                if not found:
                    logging.error(("Tried to update referral type %s for referral %s in case %s "
                                   "but it didn't exist! Nothing will be done about this.") % \
                                   update_block[const.REFERRAL_TAG_TYPE], 
                                   referral_block[const.REFERRAL_TAG_ID],
                                   self.case_id)
        
                        
        
        
    def apply_updates(self, update_action):
        """
        Applies updates to a case
        """
        if hasattr(update_action, "type") and update_action.type:
            self.type = update_action.type
        if hasattr(update_action, "name") and update_action.name:
            self.name = update_action.name
        if hasattr(update_action, "opened_on") and update_action.opened_on: 
            self.opened_on = update_action.opened_on
        
        for item in update_action.dynamic_properties():
            if item not in const.CASE_TAGS:
                self[item] = update_action[item]
        
    def apply_close(self, close_action):
        self.closed = True
        self.closed_on = datetime.combine(close_action.visit_date, time())
        self.actions.append(close_action)
        
    def save(self):
        """
        Override save to support calling it when this is part of a larger
        patient object.
        """
        # Again, this is pretty magical and wacky, but it makes our 
        # lives a lot easier.  When this is part of a patient, we 
        # update that patient and save it, otherwise we just save
        # as usual.
        if hasattr(self, "patient") and self.patient is not None:
            self.patient.update_cases([self,])
            self.patient.save()
        else:
            super(CommCareCase, self).save()

class PatientCase(CaseBase, PatientQueryMixin, UnicodeMixIn):
    """
    This is a patient (bhoma) case.  This case tracks the overall 
    problem and outcome of the problem for the patient.   Inside 
    it are commcare cases, which represent individal issues inside
    the case. 
    
    
    Properties the commcare cases inherit from this one:
    
    this object --> inner cc case
    type --> type
    _id --> external_id 
    """
    
    encounter_id = StringProperty() # encounter that created the case
    
    # patient associated with the case (this is typically redundant since the 
    # case is inside the patient, but we store it for convenience)
    patient_id = StringProperty()
    
    # current status, this is a readable representation of the state of the 
    # case that can be used in displaying it.  
    # TODO: should status be removed and calculated?
    status = StringProperty()  
    
    # final outcome (if any).  Presumably this is used in reporting.
    outcome = StringProperty() 
    
    
    ltfu_date = DateProperty()        # date the case is lost to follow-up
    
    send_to_phone = BooleanProperty() # should this case be sent to the phone?
    send_to_phone_reason = StringProperty() # if sent to phone, why?
    
    # at most one open cc case at any time
    # these are like referrals
    commcare_cases = SchemaListProperty(CommCareCase) 
    
    def __unicode__(self):
        return ("%s:%s" % (self.get_id, self.opened_on))

    _encounter = None
    def get_encounter(self):
        if not self._encounter:
            self._encounter = Encounter.view("encounter/in_patient", key=self.encounter_id).one()
        return self._encounter
    
    def status_display(self):
        if self.closed:
            return value_for_display(self.outcome) if self.outcome else "unknown outcome"
        else:
            return value_for_display(self.status) if self.status else "unknown status"
    
    def get_latest_commcare_case(self):
        if len(self.commcare_cases) > 0:
            cases = [case for case in self.commcare_cases]
            return sorted(cases, key=lambda case: case.opened_on, reverse=True)[0]
        return None
    
    @property
    def formatted_outcome(self):
        if self.outcome:
            return value_for_display(self.outcome)

    def will_go_to_phone(self):
        return self.send_to_phone and not self.closed
    
    def will_go_to_phone_reason(self):
        if self.will_go_to_phone():
            return self.send_to_phone_reason
        elif self.closed:
            return "case closed"
        else:
            return "" # ?
    
    def manual_close(self, outcome, date):
        """
        Closes a case with the specified outcome on the specified date
        """
        # close any open inner commcare cases
        for case in self.commcare_cases:
            if not case.closed:
                close_action = CommCareCaseAction.new_close_action(date)
                case.apply_close(close_action)
        # and the patient case 
        self.outcome = outcome
        self.closed = True
        self.closed_on = date
            
    
class PregnancyDatesNotSetException(Exception):
    pass


class Pregnancy(Document, UnicodeMixIn):
    """
    Data that encapsulates a pregnancy.  Consists of a group of pregnancy 
    encounters that link together to form a single object.
    """
    
    edd = DateProperty()
    
    # the anchor form "anchors" the pregnancy.  once set, it's set for
    # all time.  This prevents problems with regenerating pregnancies
    # causing bad/new case ids which break all sorts of things
    anchor_form_id = StringProperty()
    
    # ids of the other (non-anchor) forms.  Again, once mapped, the form
    # stays
    other_form_ids = StringListProperty()
    
    closed = BooleanProperty(default=False)
    closed_on = DateTimeProperty()
    outcome = StringProperty()
    
    def __init__(self, *args, **kwargs):
        super(Pregnancy, self).__init__(*args, **kwargs)
        self._encounters = []
        
    def __unicode__(self):
        return "Pregancy: (due: %s)" % (self.edd)
    
    class Meta:
        app_label = 'case'

    @property
    def form_ids(self):
        ret = []
        if self.anchor_form_id:
            ret.append(self.anchor_form_id)
        ret.extend(self.other_form_ids)
        return ret
    
    def contains(self, encounter):
        return encounter.xform_id in self.form_ids
    
    def get_anchor_encounter(self):
        if not self.anchor_form_id:
            raise Exception("Can't get a case id from an unanchored pregnancy!")
        for enc in self.sorted_encounters():
            if enc.xform_id == self.anchor_form_id:
                return enc
        raise Exception("Form with id %s not found in pregnancy!" % self.anchor_form_id)
    
    def _load_encounter_data(self):
        """
        Loads the encounters into this.  
        """
        def _clear_encounters(self):
            self._encounters = []
        
        if len(self._encounters) == 0 and (self.anchor_form_id or self.other_form_ids):
            self._encounters = []
            if self.anchor_form_id:
                anchor = Encounter.view("encounter/in_patient_by_form", key=self.anchor_form_id).one()
                # this typically means we're in reprocessing mode, just clear the encounters
                # and try again next time.
                if not anchor: 
                    return _clear_encounters(self)
                self._add_encounter(anchor)
                
            for form_id in self.other_form_ids:
                enc = Encounter.view("encounter/in_patient_by_form", key=form_id).one()
                # this typically means we're in reprocessing mode, just clear the encounters
                # and try again next time.
                if not enc:
                    return _clear_encounters(self)
                self._add_encounter(enc)
        
    def is_anchored(self):
        return True if self.anchor_form_id else False
    
    def pregnancy_dates_set(self):
        return self.edd is not None
    
    @property
    def lmp(self):
        if self.edd:
            return lmp_from_edd(self.edd)
        raise PregnancyDatesNotSetException()
    
    def get_first_visit_date(self):
        if self.sorted_encounters():
            return self.sorted_encounters()[0].visit_date
        return Encounter.get_visit_date(self.sorted_xforms()[0])
    
    def get_last_visit_date(self):
        if self.sorted_encounters():
            return self.sorted_encounters()[-1].visit_date
        return Encounter.get_visit_date(self.sorted_xforms()[-1])
    
    def get_start_date(self):
        if self.pregnancy_dates_set():
            return self.lmp - timedelta(days=DAYS_BEFORE_LMP_START)
        return self.get_first_visit_date()
        
    def get_end_date(self):
        if self.pregnancy_dates_set():
            return self.edd + timedelta(days=DAYS_AFTER_EDD_END)
        return self.get_last_visit_date()
    
    def sorted_xforms(self):
        # TODO: cache.  efficiency.
        forms = []
        for form_id in self.form_ids:
            forms.append(CXFormInstance.get(form_id))
        return sorted(forms, key=lambda form: Encounter.get_visit_date(form))
    
    def sorted_encounters(self):
        self._load_encounter_data()
        return sorted(self._encounters, key=lambda encounter: encounter.visit_date)
    
    @classmethod
    def from_encounter(cls, encounter):
        preg = Pregnancy()
        preg.add_visit(encounter)
        return preg
        
    def add_visit(self, encounter):
        self._load_encounter_data()
        self._add_encounter(encounter)
        if self.anchor_form_id != encounter.xform_id:
            self.other_form_ids.append(encounter.xform_id)
        
    def _add_encounter(self, encounter):
        # adds data from a visit.  doesn't update the couch-saved properties
        self._encounters.append(encounter)
        edd = get_edd(encounter)
        if not self.pregnancy_dates_set() and edd:
            self.edd = edd
            if not self.anchor_form_id:
                self.anchor_form_id = encounter.xform_id

        fu = get_pregnancy_followup(encounter)
        if fu.closes_case():
            self.closed = True
            self.closed_on = datetime.combine(encounter.visit_date, time())
            self.outcome = fu.get_outcome()
        
import bhoma.apps.case.signals as force_signals_import