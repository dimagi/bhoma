from django.conf.urls.defaults import *

urlpatterns = patterns('',                       
    url(r'^test/$', 'bhoma.apps.phone.views.test'),
)

