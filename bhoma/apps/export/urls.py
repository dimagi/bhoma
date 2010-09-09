from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^model/$', 'bhoma.apps.export.views.download_model', name='model_download_excel'),
)
