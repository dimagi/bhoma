from bhoma.apps.locations.models import Location
from django.conf import settings

def clinic_display_name(clinic_id):
    try:
        return Location.objects.get(slug=clinic_id).name
    except Location.DoesNotExist:
        # oops.  Should be illegal but we'll default to the code
        return clinic_id
    
def location_type(clinic_id=None):
    try:
        if clinic_id == None:
            clinic_id = settings.BHOMA_CLINIC_ID
        return Location.objects.get(slug=clinic_id).type.slug
    except (Location.DoesNotExist, AttributeError):
        return None
