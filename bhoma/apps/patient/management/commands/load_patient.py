"""
This script loads patients into the database.
"""

import os
from django.core.management.base import LabelCommand, CommandError
from bhoma.apps.patient import export

class Command(LabelCommand):
    help = "Loads a patient into couchdb"
    args = "<file>"
    label = 'patient data file'
    
    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_name = args[0]
        patient = export.import_patient_zip(file_name)
        print "successfully loaded %s" % patient.formatted_name
        #directory = args[0]
        #load_patients(directory)
                
    def __del__(self):
        pass
    
def load_patients(directory):
    from bhoma.apps.patient.models import CPatient
    count = 0
    for file in os.listdir(directory):
        fname = os.path.join(directory, file)
        if fname.endswith("zip"):
            export.import_patient_zip(fname)
            count += 1
    print "successfully loaded %s new patients" % count