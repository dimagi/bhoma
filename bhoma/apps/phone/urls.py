from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^restore/$', 'bhoma.apps.phone.views.restore'),
    url(r'^test/$', 'bhoma.apps.phone.views.test'),
    
)

