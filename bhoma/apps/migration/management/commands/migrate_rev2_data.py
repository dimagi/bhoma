from django.core.management.base import LabelCommand, CommandError
from bhoma.utils.couch.database import get_db
from bhoma.apps.patient.management.commands.shared import are_you_sure
import sys
from couchdbkit.resource import ResourceNotFound
from couchdbkit.client import Database
from bhoma.utils.couch.sync import replicate

class Command(LabelCommand):
    help = "Migrates some data to a new rev2 database."
    args = "db"
    label = ""
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage: manage.py migrate_rev2_data <old_db>')
        db = get_db()
        source_db = args[0]
        print "migrating rev1 data to from %s to %s" % (source_db, db.dbname)
        replicate(db.server, source_db, db.dbname, filter="migration/migrates_rev_2")
        print "migration complete"