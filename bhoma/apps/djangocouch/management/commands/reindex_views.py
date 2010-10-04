from django.conf import settings
from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db, get_view_names
from bhoma.utils.logging import log_exception
import logging
from datetime import datetime
from bhoma.logconfig import init_file_logging

class Command(LabelCommand):
    help = "Listens for patient conflicts and resolves them."
    args = ""
    label = ""
     
    def handle(self, *args, **options):
        db = get_db()
        log_file = settings.MANAGEMENT_COMMAND_LOG_FILE if settings.MANAGEMENT_COMMAND_LOG_FILE else settings.DJANGO_LOG_FILE
        init_file_logging(log_file, settings.LOG_SIZE,
                          settings.LOG_BACKUPS, settings.LOG_LEVEL,
                          settings.LOG_FORMAT)
        
        for view in get_view_names(db):
            starttime = datetime.now()
            logging.debug("reindexing view: %s" % view)
            print "reindexing view: %s" % view
            try:
                for val in db.view(view):
                    # we have to call it once, simulated by iterating to the first element
                    break
            except Exception, e:
                log_exception(extra_info="Problem reindexing view %s" % view)
            
            logging.debug("Elapsed time for %s: %s" % (view, datetime.now() - starttime))
            print ("Elapsed time for %s: %s" % (view, datetime.now() - starttime))
            
                
    def __del__(self):
        pass
    
