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
from bhoma.apps.patient.management.commands.shared import log_and_abort,\
    is_old_rev
from bhoma.utils.couch.changes import Change

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
        global max_seq
        max_seq = 0
        
        def update_max_seq(change):
            global max_seq
            if change.seq > max_seq: 
                max_seq = change.seq
                
        def add_form_to_patient(line):
            
            change = Change(line)
            
            # check the global max seq in this process to avoid repeating ourselves.
            if change.seq < max_seq:
                return log_and_abort(logging.DEBUG, "ignoring item %s because it's seq is old")
            update_max_seq(change)
                
            form_id = change.id
            # don't bother with deleted or old documents
            if change.deleted or is_old_rev(change): return 
                
            formdoc = CXFormInstance.get(form_id)
            pat_id = get_patient_id_from_form(formdoc)
            if pat_id is not None:
                try:
                    # this is so we don't get conflicting updates.  
                    # resolve conflicts and bump version numbers before adding forms  
                    pat_data = get_db().get(pat_id, conflicts=True)
                    if "_conflicts" in pat_data:
                        return log_and_abort(logging.INFO, "ignoring patient %s because there are still conflicts that need to be resolved" % pat_id)
                    else:
                        pat = CPatient.wrap(pat_data)
                        if pat.requires_upgrade():
                            return log_and_abort(logging.INFO, "ignoring patient %s, form %s because it is not yet upgraded to the latest version" % (pat_id, form_id))
                    found_ids = [enc.xform_id for enc in pat.encounters]
                    if form_id in found_ids and not formdoc.requires_upgrade():
                        return log_and_abort(logging.DEBUG, "Already found appropriate version of form %s in patient %s, no need to do anything" % (form_id, pat_id))
                    else:
                        print "Form %s not found in patient %s or was old.  Rebuilding the patient now" % (form_id, pat_id)
                        reprocess(pat_id)
                except ResourceNotFound, e:
                    return log_and_abort(logging.WARNING, "tried to check form %s in patient %s but patient has been deleted.  Ignoring" % (form_id, pat_id))
                    
                    
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
    
