import os
from bhoma.apps.locations.models import LocationType, Location, Point

class LoaderException(Exception):
    pass

def load_locations(file_path, log_to_console=True):
    if log_to_console: print "loading static locations from %s" % file_path
    # give django some time to bootstrap itself
    if not os.path.exists(file_path):
        raise LoaderException("Invalid file path: %s." % file_path)
    
    try:
        province_type = LocationType.objects.get(slug="provinces")
    except LocationType.DoesNotExist:
        province_type = LocationType.objects.create\
            (slug="provinces", singular="Province", plural="Provinces")

    try:
        district_type = LocationType.objects.get(slug="districts")
    except LocationType.DoesNotExist:
        district_type = LocationType.objects.create\
            (slug="districts", singular="district", plural="districts")

    csv_file = open(file_path, 'r')

    count = 0    
    for line in csv_file:
        #leave out first line
        if "name of rhc" in line.lower():
            continue
        province_name, district_name, facility_name, code, facility_type, latitude, longitude = line.split(",")

        #create/load province
        try:
            province = Location.objects.get(name=province_name, type=province_type)
        except Location.DoesNotExist:
            province = Location.objects.create(name=province_name, type=province_type, slug=code[0:2])

        #create/load district
        try:
            district = Location.objects.get(name=district_name, type=district_type)
        except Location.DoesNotExist:
            district = Location.objects.create(name=district_name, type=district_type, slug=code[0:4], parent=province)
        
        #create/load facility type    
        try:
            facility_type = facility_type.strip()
            type = LocationType.objects.get(slug=_clean(facility_type), singular=facility_type)
        except LocationType.DoesNotExist:
            type = LocationType.objects.create(slug=_clean(facility_type), singular=facility_type, plural=facility_type + "s")
        #create/load facility
        try:
            facility = Location.objects.get(slug=code)
        except Location.DoesNotExist:
            facility = Location(slug=code)
        facility.name = facility_name
        facility.parent = district
        if latitude and longitude:
            facility.point = Point.objects.get_or_create(latitude=latitude, longitude=longitude)[0]
        facility.type = type
        facility.save()
        count += 1

    if log_to_console: print "Successfully processed %s locations." % count


            
def _clean(location_name):
    return location_name.lower().strip().replace(" ", "_")[:30]