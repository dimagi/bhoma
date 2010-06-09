from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^dashboard/$', 'bhoma.apps.patient.views.dashboard', name='patient_dashboard'),
    url(r'^$', 'bhoma.apps.patient.views.search', name='patient_search'),
    url(r'^search/$', 'bhoma.apps.patient.views.search_results', name='patient_search_results'),
    url(r'^new/$', 'bhoma.apps.patient.views.new_patient', name='new_patient'),
    # url(r'^(?P<patient_id>.*)/form_finish/(?P<form_id>.*)/$', 'bhoma.apps.patient.views.form_complete', name='patient_form_complete'),
    url(r'^(?P<patient_id>.*)/$', 'bhoma.apps.patient.views.single_patient', name='single_patient'),

)

