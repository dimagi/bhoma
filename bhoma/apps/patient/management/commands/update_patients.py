"""
This script dynamically updates the bhoma patients based off the contents
of xforms.
"""

from django.core.management.base import LabelCommand, CommandError
import sys
from bhoma.utils.parsing import string_to_boolean
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.processing import reprocess
from django.core.urlresolvers import reverse
from bhoma.apps.patient.management.commands.shared import are_you_sure

WARNING_TEXT = """
======================================================================
                            READ THIS!!!
About to regenerate patient data.  This will update all your patient 
documents and could cause unplanned side effects.  It is recommended 
that you back up your database before running this command.  We try 
our best to ensure everything is backed up but don't make any promises 
about what might happen to your data after you run this.
======================================================================
Are you sure you know what you're doing and want to proceed?

(yes or no):  """ 

class Command(LabelCommand):
    help = "Updates patient case and encounter data from xforms"
    
    def handle(self, *args, **options):
        
        if not are_you_sure(WARNING_TEXT):
            print "Okay.  Good call -- safety first!  Goodbye."
            sys.exit()
        else:
            all_patients = get_db().view("patient/ids").all()
            successfully_processed = []
            failed = []
            NOTIFICATION_INCREMENT = 10
            count = 0
            total_pats = len(all_patients)
            for result in all_patients:
                if count % NOTIFICATION_INCREMENT == 0:
                    print "processing patient %s of %s" % (count, total_pats)
                pat_id = result["key"]
                count = count + 1
                if reprocess(pat_id):
                    successfully_processed.append(pat_id)
                else:
                    failed.append(pat_id)
            
            if failed:
                print "======= failed patients ========\n" + "\n".join(failed)
                print "Unable to process the above patients.  Lookup these " \
                      "patient ids by visiting the urls like so: %s" % (reverse("single_patient", args=(failed[0],)))
            print "Successfully processed %s patients.  There were problems with %s patients." % \
                    (len(successfully_processed), len(failed))
            
    def __del__(self):
        pass
