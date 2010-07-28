from __future__ import absolute_import
from datetime import datetime
from couchdbkit.ext.django.schema import *
from bhoma.apps.patient.models.couch import CPhone
from couchdbkit.schema.properties_proxy import SchemaListProperty
from django.contrib.auth.models import User
from bhoma.utils.django.database import get_unique_value


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


def get_django_user_object(chw):
    """From a CHW object, automatically build a django user"""
    user = User()
    user.username = get_unique_value(User.objects, "username", chw.username, "")
    user.set_password(chw.password)
    user.first_name = chw.first_name
    user.last_name  = chw.last_name
    user.email = ""
    user.is_staff = False # Can't log in to admin site
    user.is_active = True # Activated upon receipt of confirmation
    user.is_superuser = False # Certainly not
    user.last_login =  datetime(1970,1,1)
    user.date_joined = datetime.utcnow()
    return user