from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r'^sofa/(?P<object_id>.*)/$', 'bhoma.apps.djangocouch.views.sofa', name='sofa'),
)
