from __future__ import absolute_import

from couchdbkit.ext.django.schema import *
from bhoma.apps.case import const
from bhoma.utils import parsing
from couchdbkit.schema.properties_proxy import SchemaListProperty

"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.

For details on casexml check out:
http://bitbucket.org/javarosa/javarosa/wiki/casexml
"""

class CCaseBase(Document):
    """
    Base class for cases and referrals.
    """
    opened_on = DateTimeProperty()
    modified_on = DateTimeProperty()
    closed_on = DateTimeProperty()
    type = StringProperty()
    closed = BooleanProperty(default=False)

    class Meta:
        app_label = 'case'


class CCaseAction(Document):
    """
    An atomic action on a case.  Either a create, update, or close block in
    the xml.
    """
    action_type = StringProperty(required=True)
    date = DateTimeProperty()
    
    # the following fields are for updates that modify the 
    # fields of the case itself
    type = StringProperty()
    name = StringProperty()
    opened_on = DateTimeProperty()
    
    @classmethod
    def from_action_block(cls, action, date, action_block):
        if not action in const.CASE_ACTIONS:
            raise ValueError("%s not a valid case action!")
        
        action = CCaseAction(action_type=action, date=date)
        
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

    
class CReferral(CCaseBase):
    """
    A referral, taken from casexml.  In our world referrals are
    just cases with type "referral", but in JavaRosa they are 
    different objects.  This model helps to reconcile those 
    differences.
    
    """
    
    followup_on = DateTimeProperty()
    
    # Referrals have top-level couch guids, but this id is important
    # to the phone, so we keep it here.  This is _not_ globally unique
    # but case_id/referral_id/type should be.  
    # (in our world: case_id/referral_id/type)
    referral_id = StringProperty() 
    
    class Meta:
        app_label = 'case'

    def apply_updates(self, block):
        if not self.tag == block[const.REFERRAL_TAG_TYPE]:
            raise ValueError("Can only update from a block with matching type!")
        
        if const.REFERRAL_TAG_DATE_CLOSED in block:
            self.closed = True
            self.closed_on = parsing.string_to_datetime(block[const.REFERRAL_TAG_DATE_CLOSED])
            
            
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
                    ref.apply_updates(update_block)
        
        return ref_list
        
class CCase(CCaseBase):
    """
    A case, taken from casexml.  This represents the latest
    representation of the case - the result of playing all
    the actions in sequence.
    """
    
    case_id = StringProperty()
    external_id = StringProperty()
    referrals = SchemaListProperty(CReferral())
    actions = SchemaListProperty(CCaseAction())
    name = StringProperty()
    user_id = StringProperty()
    
    class Meta:
        app_label = 'case'

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
        create_action = CCaseAction.from_action_block(const.CASE_ACTION_CREATE, opened_on, create_block)
        
        case = CCase(case_id=id, opened_on=opened_on, modified_on=opened_on, 
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
            update_action = CCaseAction.from_action_block(const.CASE_ACTION_UPDATE, 
                                                          mod_date, update_block)
            self.apply_updates(update_action)
            self.actions.append(update_action)
        
        if const.CASE_ACTION_CLOSE in case_block:
            close_block = case_block[const.CASE_ACTION_CLOSE]
            close_action = CCaseAction.from_action_block(const.CASE_ACTION_CLOSE, 
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
        
        