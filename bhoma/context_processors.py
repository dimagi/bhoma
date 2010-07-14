from django.conf import settings
from bhoma.apps.locations.models import Location

def clinic(request):
    """
    Sets the clinic id in the request object
    """
    try:
        clinic = Location.objects.get(slug__iexact=settings.BHOMA_CLINIC_ID)
        return {"clinic": clinic }
    except Location.DoesNotExist:
        return {}