from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^duplicates/$', 'bhoma.apps.case.views.duplicates', name='duplicate_cases'),
    url(r'^duplicates/(?P<case_id>\w+)/$', 'bhoma.apps.case.views.duplicate_details', 
        name='duplicate_case_details'),
)