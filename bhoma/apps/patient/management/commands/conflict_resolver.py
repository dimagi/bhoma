from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db
from couchdbkit.consumer import Consumer
from bhoma.const import FILTER_CONFLICTING_PATIENTS
from bhoma.apps.patient import conflicts
from bhoma.utils.logging import log_exception
import logging

class Command(LabelCommand):
    help = "Listens for changes and does something about them."
    args = ""
    label = ""
     
    def handle(self, *args, **options):
        db = get_db()
        c = Consumer(db)
        
        def resolve_conflict(line):
            try:
                patient_id = line["id"]
                if conflicts.resolve_conflicts(patient_id):
                    logging.debug("resolved conflict for %s" % patient_id)
                else:
                    logging.warn("no conflict found when expected in patient: %s" % patient_id)
            except Exception, e:
                log_exception(e)
            
        c.register_callback(resolve_conflict)
        # Go into receive loop waiting for any conflicting patients to
        # come in.
        c.wait(heartbeat=5000, filter=FILTER_CONFLICTING_PATIENTS) 
                
    def __del__(self):
        pass
    
