from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db
from couchdbkit.consumer import Consumer
from bhoma.const import FILTER_PATIENTS, FILTER_XFORMS
from bhoma.utils.logging import log_exception
import logging
import time
from bhoma.apps.patient.models.couch import CPatient
from bhoma.apps.patient.processing import reprocess, get_patient_id_from_form
from bhoma.logconfig import init_file_logging
from django.conf import settings
from couchdbkit.resource import ResourceNotFound
from bhoma.apps.xforms.models import CXFormInstance

class Command(LabelCommand):
    help = "Listens for new patient forms and updates patients, if they aren't found in the patient."
    args = ""
    label = ""
    
    def handle(self, *args, **options):
        db = get_db()
        c = Consumer(db)
        log_file = settings.MANAGEMENT_COMMAND_LOG_FILE if settings.MANAGEMENT_COMMAND_LOG_FILE else settings.DJANGO_LOG_FILE
        init_file_logging(log_file, settings.LOG_SIZE,
                          settings.LOG_BACKUPS, settings.LOG_LEVEL,
                          settings.LOG_FORMAT)
        
        def add_form_to_patient(line):
            form_id = line["id"]
            # don't bother with deleted documents
            if "deleted" in line and line["deleted"]:
                return 
            try:
                formdoc = CXFormInstance.get(form_id)
            except ResourceNotFound, e:
                logging.warning("tried to check form %s but has been deleted.  Ignoring" % form_id)
                print ("tried to check form %s but has been deleted.  Ignoring" % form_id)
                return 
            pat_id = get_patient_id_from_form(formdoc)
            if pat_id is not None:
                try:
                    pat = CPatient.get(pat_id)
                except ResourceNotFound, e:
                    logging.warning("tried to check form %s in patient %s but patient has been deleted.  Ignoring" % (form_id, pat_id))
                    print ("tried to check form %s in patient %s but patient has been deleted.  Ignoring" % (form_id, pat_id))
                    return 
                found_ids = [enc.xform_id for enc in pat.encounters]
                if form_id in found_ids and not formdoc.requires_upgrade():
                    logging.debug("Already found appropriate version of form %s in patient %s, no need to do anything" % (form_id, pat_id))
                else:
                    print "Form %s not found in patient %s or was old.  Rebuilding the patient now" % (form_id, pat_id)
                    reprocess(pat.get_id)
                    
        c.register_callback(add_form_to_patient)
        # Go into receive loop waiting for any conflicting patients to
        # come in.
        while True:
            try:
                c.wait(heartbeat=5000, filter=FILTER_XFORMS)
            except Exception, e:
                time.sleep(10)
                log_exception(e, "caught exception in patient formslistener")
                logging.warn("caught exception in patient formslistener: %s, sleeping and restarting" % e)
            
                
    def __del__(self):
        pass
    
