from django.core.management.base import LabelCommand, CommandError
from dimagi.utils.couch.database import get_db
from couchdbkit.resource import ResourceNotFound
from couchdbkit.client import Database
from bhoma.utils.sync import replicate
import os
from django.conf import settings
from couchdbkit.loaders import FileSystemDocLoader

class Command(LabelCommand):
    help = "Migrates some data to a new rev2 database."
    args = "db"
    label = ""
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage: manage.py migrate_rev2_data <old_db>')
        db = get_db()
        source_db = args[0]
        # the source db needs to have the migration views built so just force-sync the 
        # design doc
        print "prepping source database %s" % source_db
        source = db.server.get_or_create_db(source_db)
        path_to_migration = os.path.join(settings.BHOMA_ROOT_DIR, "apps", "migration")
        loader = FileSystemDocLoader(path_to_migration, "_design", design_name="migration")
        loader.sync(source)
        
        print "migrating rev1 data to from %s to %s" % (source_db, db.dbname)
        replicate(db.server, source_db, db.dbname, filter="migration/migrates_rev_2")
        print "migration complete"