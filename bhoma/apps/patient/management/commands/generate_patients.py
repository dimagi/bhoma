"""
This script loads random patients into the database.
"""

from django.core.management.base import LabelCommand, CommandError

class Command(LabelCommand):
    help = "Loads patients into couchdb"
    args = "<number_of_patients>, <clinic id>"
    label = 'Number of patients'
    
    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        num_patients = int(args[0])
        clinic_id = args[1] if len(args) == 2 else None
        create_patients(num_patients, clinic_id)
                
    def __del__(self):
        pass
    
def create_patients(count, clinic_id):
    from bhoma.utils.data import random_person, random_clinic_id
    from bhoma.apps.patient.models import CPatient
    if clinic_id is None:  
        print "no clinic specified, will randomly assign ids"
    CPatient.get_db()
    for i in range(count):
        p = random_person()
        this_clinic_id = clinic_id if clinic_id else random_clinic_id()
        p.clinic_ids = [this_clinic_id,]
        p.save()
    print "successfully generated %s new patients" % count