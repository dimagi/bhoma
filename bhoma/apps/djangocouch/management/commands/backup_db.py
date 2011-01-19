from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from bhoma.utils.couch.database import get_db, get_view_names
from bhoma.utils.logging import log_exception
import logging
from datetime import datetime
from bhoma.logconfig import init_file_logging
from bhoma.utils.parsing import string_to_boolean
from bhoma.apps.patient.management.commands.shared import are_you_sure
import sys
from couchdbkit.resource import ResourceNotFound
from optparse import make_option
from couchdbkit.client import Database

WARNING = \
"""Existing database %s will be deleted prior to running.  
This operation is PERMANENT and IRREVERSIBLE.

Are you sure you want to do this? (y/n)  """

class Command(LabelCommand):
    help = "Backs up the local couch db."
    args = "db"
    label = ""
    option_list = LabelCommand.option_list + \
        (make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind. '    \
                 'Databases will be deleted without warning.'),)

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage: manage.py backup_db <backup>')
        source = get_db()
        server = source.server
        backupname = args[0]
        if backupname in server:
            should_proceed = are_you_sure(WARNING % backupname) if options["interactive"] else True
            if not should_proceed:
                print "Ok, aborting"
                sys.exit()
            server.delete_db(backupname)
            print "deleted %s" % backupname
        
        print "backing up %s to %s" % (source.dbname, backupname)        
        server.create_db(backupname)
        server.replicate(source.dbname, backupname)
        print "successfully backed up %s to %s" % (source.dbname, backupname)
        backup = server.get_or_create_db(backupname)
        print "source: %s\n\nbackup: %s" %  (source.info(), backup.info())