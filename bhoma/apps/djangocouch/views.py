from django.conf import settings
from django.http import HttpResponseRedirect

def sofa(req, object_id):
    """
    Django redirect to a sofa view.  This is really helpful during debugging
    and development but should not be used in any sort of production server
    """
    return HttpResponseRedirect("%s/_utils/document.html?%s/%s" % \
                                settings.BHOMA_COUCH_SERVER, 
                                settings.BHOMA_COUCH_DATABASE_NAME,
                                object_id)
    