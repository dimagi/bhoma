from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^test/$', 'bhoma.apps.phone.views.test'),
    url(r'^restore/$', 'bhoma.apps.phone.views.restore'),
    url(r'^restore/caseless/$', 'bhoma.apps.phone.views.restore_caseless'),
    url(r'^post/$', 'bhoma.apps.phone.views.post'),
    url(r'^logs/$', 'bhoma.apps.phone.views.logs', name="phone_sync_logs"),
    url(r'^logs/single/(?P<chw_id>\w+)/$', 'bhoma.apps.phone.views.logs_for_chw', name="phone_sync_logs_for_chw"),
    url(r'^case_xml_for_patient/(?P<patient_id>\w+)/$', 'bhoma.apps.phone.views.patient_case_xml',
        name="patient_case_xml")
    
)

