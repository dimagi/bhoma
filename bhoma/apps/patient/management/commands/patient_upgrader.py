from django.core.management.base import LabelCommand
from dimagi.utils.couch.database import get_db
from couchdbkit.consumer import Consumer
from bhoma.const import FILTER_PATIENTS
import logging
import time
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.patient.processing import reprocess
from bhoma.logconfig import init_file_logging
from django.conf import settings
from couchdbkit.resource import ResourceNotFound
from bhoma.apps.patient.management.commands.shared import log_and_abort
from dimagi.utils.couch.changes import Change

class Command(LabelCommand):
    help = "Listens for patient edits and upgrades patients, if necessary."
    args = ""
    label = ""
    
    def handle(self, *args, **options):
        db = get_db()
        c = Consumer(db)
        log_file = settings.MANAGEMENT_COMMAND_LOG_FILE if settings.MANAGEMENT_COMMAND_LOG_FILE else settings.DJANGO_LOG_FILE
        init_file_logging(log_file, settings.LOG_SIZE,
                          settings.LOG_BACKUPS, settings.LOG_LEVEL,
                          settings.LOG_FORMAT)
        problem_patients = [] # keep this list so we don't get caught in an infinite loop
        def upgrade_patient(line):
            change = Change(line)
            # don't bother with deleted or old documents
            if change.deleted or not change.is_current(db): return 
            patient_id = change.id
            try:
                if patient_id in problem_patients:
                    return log_and_abort(logging.DEBUG, "skipping problem patient: %s" % patient_id)
                
                pat_data = get_db().get(patient_id, conflicts=True)
                # this is so we don't get conflicting updates.  resolve conflicts before bumping version numbers.  
                if "_conflicts" in pat_data:
                    return log_and_abort(logging.INFO, "ignoring patient %s because there are still conflicts that need to be resolved" % patient_id)
                else:
                    pat = CPatient.wrap(pat_data)
                    if pat.requires_upgrade():
                        print "upgrading patient: %s" % patient_id
                        logging.debug("upgrading patient: %s" % patient_id)
                        if not reprocess(pat.get_id):
                            log_and_abort(logging.ERROR, "problem upgrading patient %s!" % patient_id)
                            problem_patients.append(patient_id)

            except Exception, e:
                logging.exception("problem upgrading patient (id: %s)" % patient_id)
                problem_patients.append(patient_id)
                
        
        c.register_callback(upgrade_patient)
        # Go into receive loop waiting for any conflicting patients to
        # come in.
        while True:
            try:
                c.wait(heartbeat=5000, filter=FILTER_PATIENTS)
            except Exception, e:
                time.sleep(10)
                logging.warn("caught exception in conflict resolver: %s, sleeping and restarting" % e)
            
                
    def __del__(self):
        pass
    
