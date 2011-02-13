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
    (r'^couchlog/', include("bhoma.apps.couchlog.urls")),
    (r'^encounter/', include("bhoma.apps.encounter.urls")),
    (r'^export/', include("bhoma.apps.export.urls")),
    (r'^patient/', include("bhoma.apps.patient.urls")),
    (r'^phone/', include("bhoma.apps.phone.urls")),
    (r'^phonelog/', include("bhoma.apps.phonelog.urls")),
    (r'^reports/', include("bhoma.apps.reports.urls")),
    (r'^xforms/', include("bhoma.apps.xforms.urls")),
    
)

media_prefix = settings.MEDIA_URL.strip("/")
def mk_static_urlpattern(module_suffix, static_dir):
    return patterns("", url(
        "^%s/%s/(?P<path>.*)$" % (media_prefix, module_suffix),
        "django.views.static.serve",
        {"document_root": static_dir}
    ))

# magic static server
for module_name in settings.INSTALLED_APPS:

    # leave django contrib apps alone. (many of them include urlpatterns
    # which shouldn't be auto-mapped.) this is a hack, but i like the
    # automatic per-app mapping enough to keep it. (for now.)
    if module_name.startswith("django."):
        continue

    # attempt to import this app's urls module
    module = try_import("%s.urls" % (module_name))
    if not hasattr(module, "urlpatterns"): continue

    # if the MEDIA_URL does not contain a hostname (ie, it's just an
    # http path), and we are running in DEBUG mode, we will also serve
    # the media for this app via this development server. in production,
    # these files should be served directly
    if settings.DEBUG or settings.DJANGO_SERVE_STATIC_MEDIA: 
        if not settings.MEDIA_URL.startswith("http://"):

            module_suffix = module_name.split(".")[-1]

            # does urls.py have a sibling "static" dir? (media is always
            # served from "static", regardless of what MEDIA_URL says)
            module_path = os.path.dirname(module.__file__)
            static_dir = "%s/static" % (module_path)

            if os.path.exists(static_dir):
                # map to {{ MEDIA_URL }}/appname
                urlpatterns += mk_static_urlpattern(module_suffix, static_dir)
