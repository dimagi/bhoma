from couchdbkit import *

class CDistrict(Document):
    slug = StringProperty()
    name = StringProperty()

class CClinic(Document):
    slug = StringProperty()
    name = StringProperty()
    district_id = StringProperty()
    
class CPatient(Document):
    first_name = StringProperty()
    middle_name = StringProperty()
    last_name = StringProperty()
    birthdate = DateProperty()
    birthdate_estimated = BooleanProperty()
    gender = StringProperty()
    clinic_id = StringProperty()
