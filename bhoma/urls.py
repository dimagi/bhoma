from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

import os
import os.path
from dimagi.utils.modules import try_import
# Uncomment the next two lines to enable the admin:
admin.autodiscover()

# override the 500 handler with a smarter version
handler500 = 'bhoma.apps.webapp.views.server_error'
handler404 = 'bhoma.apps.webapp.views.not_found'

urlpatterns = patterns('',
    # Example:
    # (r'^bhoma/', include('bhomalite.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/webapp/images/favicon.png'}),

    # this must come before the webapp/ and xforms/ urls
    (r'^touchforms/', include('touchforms.formplayer.urls')),
    
    (r'^', include("bhoma.apps.webapp.urls")),
    (r'^case/', include("bhoma.apps.case.urls")),
    (r'^chw/', include("bhoma.apps.chw.urls")),
    (r'^couch/', include("djangocouch.urls")),
    (r'^couchlog/', include("couchlog.urls")),
    (r'^encounter/', include("bhoma.apps.encounter.urls")),
    (r'^patient/', include("bhoma.apps.patient.urls")),
    (r'^phone/', include("bhoma.apps.phone.urls")),
    (r'^phonelog/', include("bhoma.apps.phonelog.urls")),
    (r'^reports/', include("bhoma.apps.reports.urls")),
    (r'^xforms/', include("bhoma.apps.xforms.urls")),
    (r'^export/', include("couchexport.urls")),
    (r'^downloads/', include("soil.urls")),
    
)

if settings.DEBUG or settings.DJANGO_SERVE_STATIC_MEDIA: 
    urlpatterns += patterns('staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )

