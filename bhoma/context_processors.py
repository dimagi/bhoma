from django.conf import settings
from bhoma.apps.locations.models import Location
from bhoma.apps.webapp.config import get_current_site

def clinic(request):
    """
    Sets the clinic id in the request object
    """
    try:
        clinic = get_current_site()

        Location.prefix = property(lambda self: self.slug[:6])

        return {"clinic": clinic}
    except Location.DoesNotExist:
        return {}
