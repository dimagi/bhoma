from __future__ import absolute_import

from couchdbkit.ext.django.schema import *

"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.

For details on casexml check out:
http://bitbucket.org/javarosa/javarosa/wiki/casexml
"""

class CCase(Document):
    """
    A case, taken from casexml.  This represents the latest
    representation of the case - the result of playing all
    the actions in sequence.
    """
    
    opened_on = DateTimeProperty()
    modified_on = DateTimeProperty()
    closed_on = DateTimeProperty()
    type = StringProperty()
    name = StringProperty()
    parent_id = StringProperty()
    user_id = StringProperty()
    closed = BooleanProperty(default=False)
    
    class Meta:
        app_label = 'case'


class CCaseAction(Document):
    """
    An atomic action on a case.  Either a create, update, or close block in
    the xml.
    """
    case_id = StringProperty(required=True)
    action_type = StringProperty(required=True)
    date = DateTimeProperty()
    
    # the following fields are for updates that modify the 
    # fields of the case itself
    type = StringProperty()
    name = StringProperty()
    opened_on = DateTimeProperty() 
    
    class Meta:
        app_label = 'case'

    
class CReferral(CCase):
    """
    A referral, taken from casexml.  In our world referrals are
    just cases with type "referral", but in JavaRosa they are 
    different objects.  This model helps to reconcile those 
    differences.
    
    We use the "parent_id" field to store the case creating 
    the referrals
    """
    
    followup_on = DateTimeProperty()
    
    # Referrals have top-level couch guids, but this id is important
    # to the phone, so we keep it here.  This is _not_ globally unique
    # but case_id/referral_id/type should be.  
    # (in our world: parent_id/referral_id/type)
    referral_id = StringProperty() 
    # since type will always be "referral" we need a separate type
    # to keep track of
    referral_type = StringProperty() 
    
    class Meta:
        app_label = 'case'
