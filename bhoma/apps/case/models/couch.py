from __future__ import absolute_import

from couchdbkit.ext.django.schema import *
from bhoma.apps.case import const
from bhoma.utils import parsing
from couchdbkit.schema.properties_proxy import SchemaListProperty
import logging
from bhoma.apps.patient.mixins import PatientQueryMixin
from bhoma.apps.encounter.models.couch import Encounter

"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.

For details on casexml check out:
http://bitbucket.org/javarosa/javarosa/wiki/casexml
"""

class CaseBase(Document):
    """
    Base class for cases and referrals.
    """
    opened_on = DateTimeProperty()
    modified_on = DateTimeProperty()
    closed_on = DateTimeProperty()
    type = StringProperty()
    closed = BooleanProperty(default=False)
    # when a case is closed automatically or by a chw, we use this to 
    # track whether it's been recorded into the paper system.
    recorded = BooleanProperty(default=False) 
    
    
    class Meta:
        app_label = 'case'

class CActionBase(Document):
    """
    An atomic action on something (case, referral, followup).
    """
    #action_type = StringProperty(required=True)
    #date = DateTimeProperty()
    pass

    class Meta:
        app_label = 'case'

class CReferralAction(CActionBase):
    """
    An atomic action on a referral.
    """
    # not sure we need these
    pass

class CommCareCaseAction(CActionBase):
    """
    An atomic action on a case. Either a create, update, or close block in
    the xml.  
    """
    
    # the following fields are for updates that modify the 
    # fields of the case itself
    type = StringProperty()
    name = StringProperty()
    opened_on = DateTimeProperty()
    
    @classmethod
    def from_action_block(cls, action, date, action_block):
        if not action in const.CASE_ACTIONS:
            raise ValueError("%s not a valid case action!")
        
        action = CommCareCaseAction(action_type=action, date=date)
        
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
    actions = SchemaListProperty(CReferralAction())
    
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
    the actions in sequence.
    """
    
    external_id = StringProperty()
    encounter_id = StringProperty()
    referrals = SchemaListProperty(CReferral)
    actions = SchemaListProperty(CommCareCaseAction)
    name = StringProperty()
    outcome = StringProperty()
    
    class Meta:
        app_label = 'case'
        
    @property
    def formatted_outcome(self):
        if self.outcome:
            return self.outcome.replace("_", " ")
        return ""
        
    
    def _get_case_id(self):
        return self._id
    
    def _set_case_id(self, value):
        if getattr(self, "_id", None) is not None and self._id != value:
            raise Exception("can't change case id once it has been set!")
        self._id = value
        
    case_id = property(_get_case_id, _set_case_id)
    
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
        create_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_CREATE, opened_on, create_block)
        
        case = CommCareCase(case_id=id, opened_on=opened_on, modified_on=opened_on, 
                     type=type, name=name, user_id=user_id, external_id=external_id, 
                     closed=False, actions=[create_action,])
        
        # apply initial updates, referrals and such, if present
        case.update_from_block(case_block)
        return case
    
    def update_from_block(self, case_block):
        
        mod_date = parsing.string_to_datetime(case_block[const.CASE_TAG_MODIFIED])
        if mod_date > self.modified_on:
            self.modified_on = mod_date
        
        if const.CASE_ACTION_UPDATE in case_block:
            update_block = case_block[const.CASE_ACTION_UPDATE]
            update_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_UPDATE, 
                                                          mod_date, update_block)
            self.apply_updates(update_action)
            self.actions.append(update_action)
        
        if const.CASE_ACTION_CLOSE in case_block:
            close_block = case_block[const.CASE_ACTION_CLOSE]
            close_action = CommCareCaseAction.from_action_block(const.CASE_ACTION_CLOSE, 
                                                          mod_date, close_block)
            self.apply_close(close_action)
            self.actions.append(close_action)
        
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
        if update_action.type:      self.type = update_action.type
        if update_action.name:      self.name = update_action.name
        if update_action.opened_on: self.opened_on = update_action.opened_on
        
        for item in update_action.dynamic_properties():
            if item not in const.CASE_TAGS:
                self[item] = update_action[item]
        
    def apply_close(self, close_action):
        self.closed = True
        self.closed_on = close_action.date
        
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

class PatientCase(CaseBase, PatientQueryMixin):
    """
    This is a patient (bhoma) case.  Inside it are commcare cases.
    
    Properties the commcare cases inherit from this one:
    
    this object --> inner cc case
    type --> type
    _id --> external_id 
    """
    
    """ these properties are inherited
    # all important
    opened_on = DateTimeProperty()
    modified_on = DateTimeProperty()
    closed_on = DateTimeProperty()
    type = StringProperty()
    closed = BooleanProperty(default=False)
    
    # unclear whether this should be derived from inner cases somehow.
    recorded = BooleanProperty(default=False) 
    """
    
    # encounter that created the case
    encounter_id = StringProperty()
    # patient associated with the case (this is typically redundant since the 
    # case is inside the patient, but we store it for convenience)
    patient_id = StringProperty()
    # final outcome (if any)
    outcome = StringProperty()
    
    # at most one open cc case at any time
    # these are like referrals
    commcare_cases = SchemaListProperty(CommCareCase) 
    
    """ Unused
    external_id = StringProperty()
    referrals = SchemaListProperty(CReferral)
    actions = SchemaListProperty(CommCareCaseAction)
    
    # get from encounter
    user_id = StringProperty() 
    # not sure what this should be or whether it's necessary
    name = StringProperty()
    """
    
    def __unicode__(self):
        return ("%s:%s" % (self.type, self.opened_on))

    _encounter = None
    def get_encounter(self):
        if not self._encounter:
            print self.encounter_id
            self._encounter = Encounter.view("encounter/in_patient", key=self.encounter_id).one()
        return self._encounter
        
    def meets_sending_criteria(self):
        """
        Whether this case should be sent out.
        """
        # TODO
        return True
    
