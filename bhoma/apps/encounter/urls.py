from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^(?P<patient_id>.*)/new/$', 'bhoma.apps.encounter.views.new_encounter', name='new_encounter'),
    url(r'^(?P<patient_id>.*)/$', 'bhoma.apps.encounter.views.encounters_for_patient', name='encounters_for_patient'),
)

