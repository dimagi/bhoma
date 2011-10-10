import os
from bhoma.apps.zones.models import ClinicZone
from couchdbkit.resource import ResourceNotFound
from bhoma.apps.locations.models import Location
from dimagi.utils.couch.database import get_db

class LoaderException(Exception):
    pass

def load_clinic_zones(file_path, purge=False, log_to_console=True):
    if purge:
        if log_to_console: print "Purging existing clinic zones!"
        zones = ClinicZone.view("zones/by_clinic", include_docs=True).all()
        get_db().bulk_delete([zone.to_json() for zone in zones])
        
    if log_to_console: print "loading static clinic zones from %s" % file_path
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    csv_file = open(file_path, 'r')
    try:
        count = failed = 0    
        updated_zones = []
        for line in csv_file:
            #leave out first line
            if "of households" in line.lower():
                continue
            district_name, facility_name, facility_code, zone_number, hhs = line.split(",")
    
            try:
                clinic = Location.objects.get(slug=facility_code)
            except:
                print "Clinic with code %s not found (%s)!" % (facility_code, facility_name)
                failed += 1
                continue
            
            zone = ClinicZone.view("zones/by_clinic", key=[clinic.slug, int(zone_number)], include_docs=True).one()
            if not zone: 
                zone = ClinicZone()
            zone.clinic_id = clinic.slug
            zone.zone = int(zone_number)
            zone.households = int(hhs)
            updated_zones.append(zone.to_json())
            count += 1
        ClinicZone.get_db().bulk_save(updated_zones)
        if log_to_console: print "Successfully processed %s zones." % count
        if log_to_console and failed: print "%s zones failed." % failed
    
    finally:
        csv_file.close()
