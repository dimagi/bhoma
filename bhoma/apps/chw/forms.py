from django import forms
from bhoma.apps.chw.models import CommunityHealthWorker
from bhoma.const import GENDERS
from django.forms.models import ModelMultipleChoiceField, ModelChoiceField
from bhoma.apps.locations.models import Location
from django.forms.widgets import PasswordInput, RadioSelect
from django.forms.fields import ChoiceField
from bhoma import const

_location_queryset = Location.objects.filter(type__slug=const.LOCATION_TYPE_CLINIC).\
                                        order_by("name")

MAX_NUMBER_OF_ZONES = 16
ZONE_CHOICES = ((i+1, "Zone %s" % (i+1)) for i in range(MAX_NUMBER_OF_ZONES))

class CHWForm(forms.Form):
    """
    Form for CHWs
    """
    id = forms.CharField(widget=forms.HiddenInput(), required=False)
    username = forms.CharField(max_length=15)
    password = forms.CharField(widget=PasswordInput())
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    gender = forms.ChoiceField(choices=GENDERS, widget=RadioSelect())
    current_clinic = ModelChoiceField(queryset=_location_queryset, required=True)
    current_clinic_zone = ChoiceField(choices=ZONE_CHOICES, required=True)
    phones = []
    
    @classmethod
    def from_instance(cls, instance):
        assert(instance.doc_type=="CommunityHealthWorker")
        return cls({"id": instance.get_id,
                    "username": instance.username,
                    "password": instance.password,
                    "first_name": instance.first_name,
                    "last_name": instance.last_name,
                    "gender": instance.gender,
                    "current_clinic": Location.objects.get(slug=instance.current_clinic_id).pk,
                    "current_clinic_zone": instance.current_clinic_zone})
            
    class Meta:
        app_label = 'chw'

    def clean_username(self):
        return self._read_only("username", "username")
    
    def clean_password(self):
        return self._read_only("password", "password")
        
    def _read_only(self, field, attr):
        id = self.cleaned_data['id']
        data = self.cleaned_data[field]
        if id and data != CommunityHealthWorker.get(id)[attr]:
            raise forms.ValidationError("Sorry, you are not allowed to change the %s!" % attr)

        # Always return the cleaned data, whether you have changed it or
        return data
