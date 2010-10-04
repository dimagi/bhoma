from django.conf import settings
from django.http import HttpResponseRedirect
from bhoma.apps.djangocouch.utils import futon_url

def futon(req, object_id):
    """
    Django redirect to a futon view.  This is really helpful during debugging
    and development but should not be used in any sort of production server
    """
    return HttpResponseRedirect(futon_url(object_id))
    