from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db
from couchdbkit.consumer import Consumer
from bhoma.const import FILTER_PATIENTS
from bhoma.utils.logging import log_exception
import logging
import time
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.patient.processing import reprocess
from bhoma.logconfig import init_file_logging
from django.conf import settings
from couchdbkit.resource import ResourceNotFound

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
        logging.error("LOG TEST!")
        problem_patients = [] # keep this list so we don't get caught in an infinite loop
        def upgrade_patient(line):
            patient_id = line["id"]
            # don't bother with deleted documents
            if "deleted" in line and line["deleted"]:
                return 
                
            try:
                if patient_id in problem_patients:
                    print "skipping problem patient: %s" % patient_id
                    logging.debug("skipping problem patient: %s" % patient_id)
                try:
                    pat = CPatient.get(patient_id)
                except ResourceNotFound, e:
                    logging.error("tried to update patient %s but has been deleted.  Ignoring" % patient_id)
                    return 
                if pat.requires_upgrade():
                    print "upgrading patient: %s" % patient_id
                    logging.debug("upgrading patient: %s" % patient_id)
                    reprocess(pat.get_id)

            except Exception, e:
                log_exception(e, extra_info="problem upgrading patient (id: %s)" % patient_id)
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
    
