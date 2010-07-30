from django import forms
from bhoma.apps.chw.models import CommunityHealthWorker
from bhoma.const import GENDERS
from django.forms.models import ModelMultipleChoiceField, ModelChoiceField
from bhoma.apps.locations.models import Location
from django.forms.widgets import PasswordInput, RadioSelect

_location_queryset = Location.objects.filter(type__slug="rural_health_center").\
                                        order_by("name")
    
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
    clinics = ModelMultipleChoiceField(queryset=_location_queryset)
    phones = []
    
    class Meta:
        app_label = 'chw'
