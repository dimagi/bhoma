from django.conf.urls.defaults import *

from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
                       url(r'^list/$', login_required(direct_to_template), 
                           {"template": "reports/report_list.html"}, name="report_list"),
                       url(r'^unrecorded/$', 'bhoma.apps.reports.views.unrecorded_referral_list', 
                           name='unrecorded_referral_list'),
)
