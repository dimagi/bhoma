from __future__ import absolute_import
from datetime import datetime
from couchdbkit.ext.django.schema import *
from bhoma.apps.patient.models.couch import CPhone
from couchdbkit.schema.properties_proxy import SchemaListProperty
from django.contrib.auth.models import User
from dimagi.utils.django.database import get_unique_value
from bhoma.apps.profile.models import BhomaUserProfile
from bhoma.apps.locations.models import Location
from bhoma.apps.locations.util import clinic_display_name
from bhoma.apps.zones.models import ClinicZone


"""
Couch models go here.  
"""

class CommunityHealthWorker(Document):
    """
    A community health worker
    """
    username = StringProperty(required=True)
    password = StringProperty(required=True)
    created_on = DateTimeProperty()
    first_name = StringProperty(required=True)
    last_name = StringProperty(required=True)
    gender = StringProperty(required=True)
    current_clinic_id = StringProperty(required=True)
    current_clinic_zone = IntegerProperty(required=True)
    clinic_ids = StringListProperty() # in the event of a transfer we want these to sync to all clinics
    phones = SchemaListProperty(CPhone())
    
    dynamic_data = {}
    
    
    @property
    def formatted_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    _zone = None
    _zone_checked = False
    def get_zone(self):
        if not self._zone_checked:
            self._zone = ClinicZone.view("zones/by_clinic", key=[self.current_clinic_id, self.current_clinic_zone],
                                         include_docs=True).one()
            self._zone_checked = True
        return self._zone
    
    @property
    def households(self):
        return [clinic_display_name(clinic_id) for clinic_id in self.clinic_ids]
    
    
    
    @property
    def current_clinic_display(self):
        return clinic_display_name(self.current_clinic_id)
                
    @property
    def clinics_display(self):
        return [clinic_display_name(clinic_id) for clinic_id in self.clinic_ids]
                
    _user = None
    _user_checked = False
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