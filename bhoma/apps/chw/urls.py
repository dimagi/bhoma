from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^$', 'bhoma.apps.chw.views.list_chws', name='manage_chws'),
    url(r'^new/$', 'bhoma.apps.chw.views.new_or_edit', name='new_chw'),
    url(r'^edit/(?P<chw_id>\w+)/$', 'bhoma.apps.chw.views.new_or_edit', name='edit_chw'),
    url(r'^view/(?P<chw_id>\w+)/$', 'bhoma.apps.chw.views.single', name='single_chw'),
    url(r'^view/(?P<chw_id>\w+)/delete/$', 'bhoma.apps.chw.views.delete', name='delete_chw'),
    url(r'^view/(?P<chw_id>\w+)/deactivate/$', 'bhoma.apps.chw.views.deactivate', name='deactivate_chw'),
    url(r'^view/(?P<chw_id>\w+)/activate/$', 'bhoma.apps.chw.views.activate', name='activate_chw'),
)

