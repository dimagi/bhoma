from __future__ import absolute_import
from datetime import datetime
from couchdbkit.ext.django.schema import *
from bhoma.apps.xforms.models.couch import CXFormInstance, Metadata
from bhoma.utils.parsing import string_to_datetime
from bhoma.const import PROPERTY_ENCOUNTER_DATE
from bhoma.apps.patient.encounters.config import CLINIC_ENCOUNTERS,\
    ENCOUNTERS_BY_XMLNS, CHW_ENCOUNTERS
from bhoma.utils.couch import uid
from couchdbkit.resource import ResourceNotFound
from bhoma.utils.logging import log_exception

"""
Couch models go here.  
"""

class Encounter(Document):
    """ 
    An encounter, representing a single form/visit with a patient.
    """
    
    created = DateTimeProperty(required=True)
    edited = DateTimeProperty(required=True)
    visit_date = DateProperty(required=True)
    type = StringProperty()
    is_deprecated = BooleanProperty()
    previous_encounter_id = StringProperty()
    xform_id = StringProperty() # id linking to the xform object that generated this
    _metadata = DictProperty()
    
    @property
    def metadata(self):
        # Couchdbkit doesn't seem to support nested schema properties so
        # just make this a dict and hide that from the pubilc api
        if self._metadata:
            return Metadata(self._metadata)
        return None
    
    dynamic_data = {}
    
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
            try:
                self._xform = CXFormInstance.get(self.xform_id)
            except ResourceNotFound, e:
                log_exception(e)
                return None
        return self._xform
    
    @classmethod 
    def get_visit_date(cls, form):
        # get a date from the form
        ordered_props = ["encounter_date", "date", "meta/TimeEnd"]
        for prop in ordered_props:
            if form.xpath(prop):
                return string_to_datetime(form.xpath(prop)).date()
        return datetime.utcnow().date()
        
        
    @classmethod
    def from_xform(cls, doc):
        """
        Create an encounter object from an xform document.
        """
        
        type = ENCOUNTERS_BY_XMLNS[doc.namespace].type \
                    if doc.namespace in ENCOUNTERS_BY_XMLNS else doc.namespace
        
        visit_date = Encounter.get_visit_date(doc)
        
        metadata = {}
        if doc.metadata:
            metadata = doc.metadata.to_dict()
        return Encounter(_id = uid.new(),
                         created=datetime.utcnow(),
                         edited=datetime.utcnow(),
                         visit_date=visit_date,
                         type=type,
                         is_deprecated=False,
                         _metadata=metadata,
                         xform_id=doc["_id"])
                         
        
    @property
    def display_type(self):
        if self.type in CLINIC_ENCOUNTERS:
            return CLINIC_ENCOUNTERS[self.type].name
        elif self.type in CHW_ENCOUNTERS:
            return CHW_ENCOUNTERS[self.type].name
        return self.type