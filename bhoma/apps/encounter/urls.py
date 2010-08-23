from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^(?P<patient_id>\w+)/$', 'bhoma.apps.encounter.views.encounters_for_patient', name='encounters_for_patient'),
    url(r'^(?P<patient_id>\w+)/(?P<encounter_id>\w+)/$', 'bhoma.apps.encounter.views.single_encounter', name='single_encounter'),
)

