from django.conf.urls.defaults import *

from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
                       url(r'^list/$', login_required(direct_to_template), 
                           {"template": "reports/report_list.html"}, name="report_list"),
                       url(r'^unrecorded/$', 'bhoma.apps.reports.views.unrecorded_referral_list', 
                           name='unrecorded_referral_list'),
                       url(r'^pi/under5/$', 'bhoma.apps.reports.views.under_five_pi', 
                           name='under_five_pi'),
                       url(r'^pi/adult/$', 'bhoma.apps.reports.views.adult_pi', 
                           name='adult_pi'),
                       url(r'^pi/pregnancy/$', 'bhoma.apps.reports.views.pregnancy_pi', 
                           name='pregnancy_pi'),
                       url(r'^pi/chw/$', 'bhoma.apps.reports.views.chw_pi', 
                           name='chw_pi'),
                        
)
