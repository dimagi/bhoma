from bhoma.apps.locations.models import Location

def clinic_display_name(clinic_id):
    try:
        return Location.objects.get(slug=clinic_id).name
    except Location.DoesNotExist:
        # oops.  Should be illegal but we'll default to the code
        return clinic_id
    
