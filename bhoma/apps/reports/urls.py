from django.conf.urls.defaults import *

from django.views.generic.simple import direct_to_template
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions

urlpatterns = patterns('',
                       url(r'^$', direct_to_template, 
                           {"template": "reports/report_list_ts.html",
                            "extra_context": {"options": TouchscreenOptions.default() }},
                            name="report_list"),
                       url(r'^summary/$', 'bhoma.apps.reports.views.clinic_summary', 
                           name='clinic_summary_report'),
                       url(r'^user_summary/$', 'bhoma.apps.reports.views.user_summary', 
                           name='user_summary_report'),
                       url(r'^unrecorded/$', 'bhoma.apps.reports.views.unrecorded_referral_list', 
                           name='unrecorded_referral_list'),
					   url(r'^mortality_register/$', 'bhoma.apps.reports.views.mortality_register', 
                           name='mortality_register'),
                       url(r'^pi/under5/$', 'bhoma.apps.reports.views.under_five_pi', 
                           name='under_five_pi'),
                       url(r'^pi/adult/$', 'bhoma.apps.reports.views.adult_pi', 
                           name='adult_pi'),
                       url(r'^pi/pregnancy/$', 'bhoma.apps.reports.views.pregnancy_pi', 
                           name='pregnancy_pi'),
                       url(r'^pi/chw/$', 'bhoma.apps.reports.views.chw_pi', 
                           name='chw_pi'),
                       url(r'^punchcard/$', 'bhoma.apps.reports.views.punchcard', 
                           name='punchcard_report'),
                       url(r'^entrytime/$', 'bhoma.apps.reports.views.entrytime', 
                           name='entrytime_report'),
                        
)
