from __future__ import absolute_import
from datetime import datetime
from couchdbkit.ext.django.schema import *
from bhoma.apps.xforms.models.couch import CXFormInstance

"""
Couch models go here.  
"""

class Encounter(Document):
    created = DateTimeProperty(required=True)
    edited = DateTimeProperty(required=True)
    type = StringProperty()
    is_deprecated = BooleanProperty()
    previous_encounter_id = StringProperty()
    xform_id = StringProperty() # id linking to the xform object that generated this
    
    class Meta:
        app_label = 'encounter'

    def __unicode__(self):
        return "%s (%s)" % (self.type, self.created)
    
    _xform = None
    def get_xform(self, invalidate_cache=False):
        """
        Get the xform that created this encounter.  Will return a cached
        copy if one is available, unless invalidate_cache is specified
        and True.
        """
        if self._xform == None or invalidate_cache:
            self._xform = CXFormInstance.get(self.xform_id)
        return self._xform
    
    @classmethod
    def from_xform(cls, doc, type):
        """
        Create an encounter object from an xform document.
        """
        return Encounter(created=datetime.utcnow(),
                         edited=datetime.utcnow(),
                         type=type,
                         is_deprecated=False,
                         xform_id=doc["_id"])