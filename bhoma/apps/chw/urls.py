from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^$', 'bhoma.apps.chw.views.list_chws', name='list_chws'),
    url(r'^new/$', 'bhoma.apps.chw.views.new', name='new_chw'),
    url(r'^view/(?P<chw_id>\w+)/$', 'bhoma.apps.chw.views.single', name='single_chw'),
)

