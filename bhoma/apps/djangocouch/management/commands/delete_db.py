from django.conf import settings
from django.core.management.base import LabelCommand
from bhoma.utils.couch.database import get_db, get_view_names
from bhoma.utils.logging import log_exception
import logging
from datetime import datetime
from bhoma.logconfig import init_file_logging
from bhoma.utils.parsing import string_to_boolean
from bhoma.apps.patient.management.commands.shared import are_you_sure
import sys
from couchdbkit.resource import ResourceNotFound

WARNING = \
"""About to delete database %s.  This operation is PERMANENT and IRREVERSIBLE.

Are you sure you want to do this? (y/n)  """
class Command(LabelCommand):
    help = "Deletes a couch db."
    args = "db"
    label = ""
     
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage: manage.py delete_db <database>')
        dbname = args[0]
        should_proceed = are_you_sure(WARNING % dbname)
        if not should_proceed:
            print "Ok, aborting"
            sys.exit()
        
        server = get_db().server
        try:
            server.delete_db(dbname)
            print "deleted %s" % dbname
        except ResourceNotFound:
            print "database %s not found.  nothing done." % dbname 