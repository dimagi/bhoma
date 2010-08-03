from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^test/$', 'bhoma.apps.patient.views.test'),
    url(r'^dashboard/$', 'bhoma.apps.patient.views.dashboard', name='patient_dashboard'),
    url(r'^$', 'bhoma.apps.patient.views.search', name='patient_search'),
    url(r'^search/$', 'bhoma.apps.patient.views.search_results', name='patient_search_results'),
    url(r'^select/$', 'bhoma.apps.patient.views.patient_select', name='patient_select'),
    # single patient stuff
    url(r'^single/(?P<patient_id>\w+)/$', 'bhoma.apps.patient.views.single_patient', name='single_patient'),
    url(r'^single/(?P<patient_id>\w+)/new/$', 
        'bhoma.apps.patient.views.choose_new_encounter', name='choose_new_patient_encounter'),
    url(r'^single/(?P<patient_id>\w+)/new/(?P<encounter_slug>\w+)/$', 
        'bhoma.apps.patient.views.new_encounter', name='new_patient_encounter'),
    url(r'^render/(?P<template>.+)/$', 'bhoma.apps.patient.views.render_content', name='patient_render'),
        
    # API patterns
    url(r'^api/lookup$', 'bhoma.apps.patient.views.lookup_by_id', name='patient_id_query'),    
    url(r'^api/match/$', 'bhoma.apps.patient.views.fuzzy_match', name='patient_fuzzy_match'),    
    
)    
     
