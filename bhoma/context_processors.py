from django.conf import settings
from bhoma.apps.locations.models import Location
from bhoma.apps.webapp.config import get_current_site
from bhoma.apps.zones.models import ClinicZone
from bhoma import const

def webapp(request):
    return {
        'clinic': context_clinic(),
        'app_version': settings.BHOMA_COMMIT_ID,
    }

def context_clinic():
    """
    Sets the clinic id in the request object
    """
    try:
        clinic = get_current_site()

        def get_prefix(self):
            """For clinic codes, convert 5020180 to 502180"""
            
            # with proper, 13-digit IDs, we don't need to manipulate the clinic prefix anymore
            #if len(self.slug) ==  7:
            #    return "%s%s" % (self.slug[:3], self.slug[4:7])
            return self.slug
        Location.prefix = property(get_prefix)

        def get_referral_prefix(self):
            """Get prefix for CHW referral codes"""
            if len(self.slug) > 6:
                return self.slug[2] + self.slug[4:6]
            return ""
        Location.ref_prefix = property(get_referral_prefix)        
        
        clinic.num_chw_zones = len(ClinicZone.view("zones/by_clinic", 
                                                   startkey=[clinic.slug],
                                                   endkey=[clinic.slug, {}]).all())
        clinic.is_clinic = clinic.type.slug == const.LOCATION_TYPE_CLINIC
        clinic.is_central = clinic.type.slug == const.LOCATION_TYPE_PROVINCE or  \
                            clinic.type.slug == const.LOCATION_TYPE_NATIONAL
        clinic.is_district = clinic.type.slug == const.LOCATION_TYPE_DISTRICT
        
        try:
            clinic.density = settings.CLINIC_POPULATION_DENSITY
        except AttributeError:
            clinic.density = 'rural'

        return clinic
    
    except Location.DoesNotExist:
        return None

