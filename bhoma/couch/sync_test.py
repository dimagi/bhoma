from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader
from models import *
import datetime
# server object
server = Server()

try:    server.delete_db("patient")
except: pass

# create database
db = server.get_or_create_db("patient")

# load views
loader = FileSystemDocsLoader("./patient_design")
loader.sync(db, verbose=True)

# associate objects to the db
CDistrict.set_db(db)
CClinic.set_db(db)
CPatient.set_db(db)

# create some objects in the primary database
dist1 = CDistrict(slug="1", name="CDistrict 1")
dist1.save()

dist2 = CDistrict(slug="2", name="CDistrict 2")
dist2.save()

clin1 = CClinic(slug="1", name="clinic 1", CDistrict_id=dist1._id)
clin2 = CClinic(slug="2", name="clinic 2", CDistrict_id=dist1._id)
clin3 = CClinic(slug="3", name="clinic 3", CDistrict_id=dist1._id)
clin4 = CClinic(slug="4", name="clinic 4", CDistrict_id=dist2._id)
clin5 = CClinic(slug="5", name="clinic 5", CDistrict_id=dist2._id)

clinics = [clin1, clin2, clin3, clin4, clin5]

for clin in clinics:  clin.save()
    
def new_patient(clinic, id):
    p = CPatient(first_name = "cory",
                middle_name = "lockwood",
                last_name = "zue %s" % id,
                birthdate = datetime.datetime.utcnow().date(),
                birthdate_estimated = False,
                gender = "m",
                clinic_id = clinic._id)
    p.save()
    return p

all_pats = []
for clin in clinics:
    for i in range(5):
        all_pats.append(new_patient(clin, len(all_pats)))

patients = CPatient.view("patient/all")

# do some sync to individual clinic dbs

print patients
for patient in patients:
    print patient