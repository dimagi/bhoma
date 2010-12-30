from django.conf import settings
from bhoma.apps.locations.models import Location
from bhoma.apps.webapp.config import get_current_site

def clinic(request):
    """
    Sets the clinic id in the request object
    """
    try:
        clinic = get_current_site()
        def get_prefix(self):
            """
            For clinic codes, convert 5020180 to 502180
            """
            if len(self.slug) ==  7:
                return "%s%s" % (self.slug[:3], self.slug[4:7])
            return self.slug    
        Location.prefix = property(get_prefix)
        return {"clinic": clinic}
    
    except Location.DoesNotExist:
        return {}

def app_version(request):
    return {'app_version': settings.BHOMA_COMMIT_ID}
