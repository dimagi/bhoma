from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^unrecorded/$', 'bhoma.apps.reports.views.unrecorded_referral_list', name='unrecorded_referral_list'),
)
