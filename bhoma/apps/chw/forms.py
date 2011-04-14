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

MAX_NUMBER_OF_ZONES = 8
ZONE_CHOICES = ((i+1, "Zone %s" % (i+1)) for i in range(MAX_NUMBER_OF_ZONES))

class CHWForm(forms.Form):
    """
    Form for CHWs
    """
    username = forms.CharField(max_length=15)
    password = forms.CharField(widget=PasswordInput())
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    gender = forms.ChoiceField(choices=GENDERS, widget=RadioSelect())
    current_clinic = ModelChoiceField(queryset=_location_queryset, required=True)
    current_clinic_zone = ChoiceField(choices=ZONE_CHOICES, required=True)
    phones = []
    
    class Meta:
        app_label = 'chw'
