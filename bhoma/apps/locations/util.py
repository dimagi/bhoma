from bhoma.apps.locations.models import Location
from django.conf import settings

def clinic_display_name(clinic_id):
    try:
        return Location.objects.get(slug=clinic_id).name
    except Location.DoesNotExist:
        # oops.  Should be illegal but we'll default to the code
        return clinic_id
    
def clinic_display(clinic_id):
    try:
        return "%s (%s)" % (Location.objects.get(slug=clinic_id).name, clinic_id)
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

def clinics_for_view():
    """
    These are used by the reports
    """
    return Location.objects.filter(type__slug="clinic").order_by("parent__name", "name")

def districts_for_view():
    """
    These are used by the reports
    """
    return Location.objects.filter(type__slug="district").order_by("name")