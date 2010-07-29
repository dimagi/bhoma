from __future__ import absolute_import
from datetime import datetime
from couchdbkit.ext.django.schema import *
from bhoma.apps.patient.models.couch import CPhone
from couchdbkit.schema.properties_proxy import SchemaListProperty
from django.contrib.auth.models import User
from bhoma.utils.django.database import get_unique_value
from bhoma.apps.profile.models import BhomaUserProfile
from bhoma.apps.locations.models import Location


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
    current_clinic_id = StringProperty()
    clinic_ids = StringListProperty() # in the event of a transfer we want these to sync to all clinics
    phones = SchemaListProperty(CPhone())
    
    dynamic_data = {}
    
    _user = None
    _user_checked = False
    
    @property
    def current_clinic_display(self):
        return _clinic_display_name(self.current_clinic_id)
                
    @property
    def clinics_display(self):
        return [_clinic_display_name(clinic_id) for clinic_id in self.clinic_ids]
                
        
    @property
    def user(self):
        """
        Get the linked django user, if there.
        """
        if not self._user_checked:
            try:
                self._user = BhomaUserProfile.objects.get(chw_id=self.get_id).user
            except BhomaUserProfile.DoesNotExist:
                pass
            self._user_checked = True
        return self._user

    class Meta:
        app_label = 'chw'

def _clinic_display_name(clinic_id):
    try:
        return Location.objects.get(slug=clinic_id).name
    except Location.DoesNotExist:
        # oops.  Should be illegal but we'll default to the code
        return clinic_id
    
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