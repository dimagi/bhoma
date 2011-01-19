from django.core.management.base import LabelCommand, CommandError
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.management.commands.shared import are_you_sure
import sys
from couchdbkit.resource import ResourceNotFound
from optparse import make_option

WARNING = \
"""About to delete database %s.  This operation is PERMANENT and IRREVERSIBLE.

Are you sure you want to do this? (y/n)  """
class Command(LabelCommand):
    help = "Deletes a couch db.  If no db specified deletes your local db"
    args = "db"
    label = ""
    option_list = LabelCommand.option_list + \
        (make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind. '    \
                 'Databases will be deleted without warning.'),)

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError('Usage: manage.py delete_db [database]')
        if len(args) == 1:
            dbname = args[0]
        else:
            dbname = get_db().dbname
        should_proceed = are_you_sure(WARNING % dbname) if options["interactive"] else True
        if not should_proceed:
            print "Ok, aborting"
            sys.exit()
        
        server = get_db().server
        try:
            server.delete_db(dbname)
            print "deleted %s" % dbname
        except ResourceNotFound:
            print "database %s not found.  nothing done." % dbname 