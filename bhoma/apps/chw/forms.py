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

ZONE_CHOICES = ((1, "Zone 1"), 
                (2, "Zone 2"), 
                (3, "Zone 3"), 
                (4, "Zone 4"), 
                (5, "Zone 5"), 
                (6, "Zone 6"))

class CHWForm(forms.Form):
    """
    Form for CHWs
    """
    username = forms.CharField(max_length=15)
    password = forms.CharField(widget=PasswordInput())
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    gender = forms.ChoiceField(choices=GENDERS, widget=RadioSelect())
    chw_id = forms.CharField(max_length=10)
    current_clinic = ModelChoiceField(queryset=_location_queryset, required=True)
    current_clinic_zone = ChoiceField(choices=ZONE_CHOICES, required=True)
    clinics = ModelMultipleChoiceField(queryset=_location_queryset)
    phones = []
    
    class Meta:
        app_label = 'chw'
