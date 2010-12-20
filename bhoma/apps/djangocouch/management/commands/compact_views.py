from django.conf import settings
from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db, get_view_names, get_design_docs
from bhoma.utils.logging import log_exception
import logging
from datetime import datetime
from bhoma.logconfig import init_file_logging

class Command(LabelCommand):
    help = "Compacts couch views."
    args = ""
    label = ""
     
    def handle(self, *args, **options):
        db = get_db()
        log_file = settings.MANAGEMENT_COMMAND_LOG_FILE if settings.MANAGEMENT_COMMAND_LOG_FILE else settings.DJANGO_LOG_FILE
        init_file_logging(log_file, settings.LOG_SIZE,
                          settings.LOG_BACKUPS, settings.LOG_LEVEL,
                          settings.LOG_FORMAT)
        
        for doc in get_design_docs(db):
            logging.debug("compacting views for app: %s" % doc.name)
            print("compacting views for app: %s" % doc.name)
            db.compact(doc.name)
                
    def __del__(self):
        pass
    
