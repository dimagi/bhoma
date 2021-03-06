from __future__ import absolute_import

import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import *
import bhoma.apps.xforms.const as const
from dimagi.utils.parsing import string_to_datetime
from dimagi.utils.couch import safe_index
from xml.etree import ElementTree
from django.utils.datastructures import SortedDict
from couchdbkit.resource import ResourceNotFound
import logging
import hashlib
from dimagi.utils.couch.database import get_db
from couchversion.models import AppVersionedDocument
from bhoma.apps.xforms.const import TAG_LOCKED

"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.
"""


class Metadata(object):
    """
    Metadata of an xform, from a meta block structured like:
        
        <Meta>
            <clinic_id />
            <TimeStart />
            <TimeEnd />
            <username />
            <user_id />
            <uid />
        </Meta>
    
    Everything is optional.
    """
    """
    clinic_id = StringProperty()
    time_start = DateTimeProperty()
    time_end = DateTimeProperty()
    username = StringProperty()
    user_id = StringProperty()
    uid = StringProperty()
    """
    clinic_id = None
    time_start = None
    time_end = None
    username = None
    user_id = None
    uid = None

    def __init__(self, meta_block):
        if const.TAG_META_CLINIC_ID in meta_block:
            self.clinic_id = str(meta_block[const.TAG_META_CLINIC_ID])
        if const.TAG_META_TIMESTART in meta_block:
            self.time_start = string_to_datetime(meta_block[const.TAG_META_TIMESTART])
        elif "time_start" in meta_block:
            self.time_start = string_to_datetime(meta_block["time_start"])
        if const.TAG_META_TIMEEND in meta_block:
            self.time_end = string_to_datetime(meta_block[const.TAG_META_TIMEEND])
        elif "time_end" in meta_block:
            self.time_end = string_to_datetime(meta_block["time_end"])
        if const.TAG_META_USERNAME in meta_block:
            self.username = meta_block[const.TAG_META_USERNAME]
        if const.TAG_META_USER_ID in meta_block:
            self.user_id = meta_block[const.TAG_META_USER_ID]
        if const.TAG_META_UID in meta_block:
            self.uid = meta_block[const.TAG_META_UID]
    
    def to_dict(self):
        return dict([(key, getattr(self, key)) for key in \
                     ("clinic_id", "time_start", "time_end",
                      "username", "user_id","uid")])

class LockedException(Exception):
    """
    Exception raised when something is locked.
    """
    pass

class CXFormInstance(AppVersionedDocument):
    """An XForms instance."""
    
    @property
    def type(self):
        return self.all_properties().get(const.TAG_TYPE, "")
        
    @property
    def version(self):
        return self.all_properties().get(const.TAG_VERSION, "")
        
    @property
    def uiversion(self):
        return self.all_properties().get(const.TAG_UIVERSION, "")
    
    @property
    def namespace(self):
        return self.all_properties().get(const.TAG_NAMESPACE, "")
    
    @property
    def metadata(self):
        if (const.TAG_META) in self.all_properties():
            meta_block = self.all_properties()[const.TAG_META]
            meta = Metadata(meta_block)
            return meta
            
        return None
    
    @property
    def sha1(self):
        # there are two ways this can be stored, one is the 
        # tag, the other is just calculating it over the actual
        # xml document
        stored_sha =  self.all_properties().get(const.TAG_SHA1, "")
        if stored_sha:
            return stored_sha
        else:
            return self.xml_sha1()
        
    def is_locked(self):
        return self.all_properties().get(const.TAG_LOCKED, False)
    
    class Meta:
        app_label = 'xforms'
    
    def __unicode__(self):
        return "%s (%s)" % (self.type, self.namespace)

    def xpath(self, path):
        """
        Evaluates an xpath expression like: path/to/node and returns the value 
        of that element, or None if there is no value.
        """
        return safe_index(self, path.split("/"))
    
        
    def found_in_multiselect_node(self, xpath, option):
        """
        Whether a particular value was found in a multiselect node, referenced
        by path.
        """
        node = self.xpath(xpath)
        return node and option in node.split(" ")
    
    def get_xml(self):
        try:
            # new way to get attachments
            return self.fetch_attachment("form.xml")
        except ResourceNotFound:
            logging.warn("no xml found for %s, trying old attachment scheme." % self.get_id)
            return self[const.TAG_XML]
    
    def xml_sha1(self):
        return hashlib.sha1(self.get_xml()).hexdigest()
    
    def has_duplicates(self):
        # TODO: should this also check the duplicate xform models?  probably
        dupe_count = get_db().view("xforms/duplicates", key=self.sha1, reduce=True).one()["value"]
        return int(dupe_count) > 1
    
    def contributes(self):
        """Whether this contributes, e.g. should be used in post-processing"""
        return not self.has_duplicates()
    
    def acquire_lock(self):
        if self.is_locked():
            raise LockedException("Already locked!")
    
    def release_lock(self):
        """
        Says that we are ready to consume this.  Used in preventing update conflicts.
        Returns True if the lock was released, false if it didn't have it in the
        first place.
        """
        # this bad hack tells the change listeners not to process the xform 
        # until this flag is removed.  This is an ugly way to drastically
        # reduce the number of conflicting updates we get on the central
        # server as all the signals fire on the newly created doc.
        # It's kind of like a lock.  That is totally unenforced.
        if self.is_locked():
            self[TAG_LOCKED] = False
            self.save()
            return True
        return False
        
    def top_level_tags(self):
        """
        Get the top level tags found in the xml, in the order they are found.
        """
        xml_payload = self.get_xml()
        element = ElementTree.XML(xml_payload)
        to_return = SortedDict()
        for child in element:
            # fix {namespace}tag format forced by ElementTree in certain cases (eg, <reg> instead of <n0:reg>)
            key = child.tag.split('}')[1] if child.tag.startswith("{") else child.tag 
            to_return[key] = self.xpath(key)
        return to_return
    
class CXFormDuplicate(CXFormInstance):
    """
    Duplicates of instances go here.
    """
    
    def save(self, *args, **kwargs):
        self["#doc_type"] = "XFormDuplicate"
        super(CXFormDuplicate, self).save(*args, **kwargs)
        
    def contributes(self):
        # by definition this should never contribute to anything. it's a duplicate
        return False
        