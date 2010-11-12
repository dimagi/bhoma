from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'bhoma.apps.couchlog.views.dashboard', name='couchlog_home'),
    url(r'^update/$', 'bhoma.apps.couchlog.views.update', name='couchlog_update'),
    url(r'^email/$', 'bhoma.apps.couchlog.views.email', name='couchlog_email'),
    url(r'^view/(?P<log_id>\w+)/$', 'bhoma.apps.couchlog.views.single', name='couchlog_single'),
    url(r'^searchdocs/$', 'bhoma.apps.couchlog.views.lucene_docs', name='lucene_docs'),
    url(r'^ajax/paging/$', 'bhoma.apps.couchlog.views.paging', name='couchlog_paging'),
    
)
