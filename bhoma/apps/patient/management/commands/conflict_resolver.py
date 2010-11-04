from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db
from couchdbkit.consumer import Consumer
from bhoma.const import FILTER_CONFLICTING_PATIENTS
from bhoma.apps.patient import conflicts
from bhoma.utils.logging import log_exception
import logging
import time
from bhoma.utils.couch.changes import Change
from bhoma.apps.patient.management.commands.shared import is_old_rev,\
    log_and_abort

class Command(LabelCommand):
    help = "Listens for patient conflicts and resolves them."
    args = ""
    label = ""
     
    def handle(self, *args, **options):
        db = get_db()
        c = Consumer(db)
        
        def resolve_conflict(line):
            try:
                change = Change(line)
                # don't bother with deleted or old documents
                if change.deleted or is_old_rev(change): 
                    return log_and_abort(logging.DEBUG, "ignoring %s because it's been deleted or is old" % change)
                if conflicts.resolve_conflicts(change.id):
                    logging.debug("resolved conflict for %s" % change.id)
                else:
                    logging.info("no conflict found when expected in patient: %s" % change.id)
            except Exception, e:
                log_exception(e)
        
        c.register_callback(resolve_conflict)
        # Go into receive loop waiting for any conflicting patients to
        # come in.
        while True:
            try:
                c.wait(heartbeat=5000, filter=FILTER_CONFLICTING_PATIENTS)
            except Exception, e:
                time.sleep(10)
                logging.warn("caught exception in conflict resolver: %s, sleeping and restarting" % e)
            
                
    def __del__(self):
        pass
    
