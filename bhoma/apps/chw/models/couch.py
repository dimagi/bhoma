from __future__ import absolute_import
from couchdbkit.ext.django.schema import *
from bhoma.apps.patient.models.couch import CPhone
from couchdbkit.schema.properties_proxy import SchemaListProperty


"""
Couch models go here.  
"""

class CommunityHealthWorker(Document):
    """
    A community health worker
    """
    username = StringProperty(required=True)
    password = StringProperty(required=True)
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    gender = StringProperty(required=True)
    chw_id = StringProperty(required=True) # human readable id
    clinic_ids = StringListProperty()
    phones = SchemaListProperty(CPhone())
    
    class Meta:
        app_label = 'chw'
