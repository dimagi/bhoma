from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'bhoma.apps.couchlog.views.dashboard', name='couchlog_home'),
    url(r'^update/$', 'bhoma.apps.couchlog.views.update', name='couchlog_update'),
)
