from django.core.management.base import BaseCommand, CommandError
from dimagi.utils.couch.database import get_db
from django.conf import settings
import sys

class Command(BaseCommand):
    help = "delete the export design doc from couchdb (should be run for clinics when upgrading to v0.2.3)"

    def handle(self, *args, **options):
        EXPORT_DDOC = "_design/export"

        active_apps = [app for (app, server) in settings.COUCHDB_DATABASES]

        if 'bhoma.apps.export' in active_apps:
            print 'export app is used on this installation; design doc not touched'
        else:
            db = get_db()

            def ddoc_exists():
                return db.doc_exist(EXPORT_DDOC)

            if not ddoc_exists():
                print 'export design doc is already deleted'
                sys.exit()

            db.delete_doc(EXPORT_DDOC)
            print 'deleting export design doc...'

            if ddoc_exists():
                print 'WARNING!! export design doc not deleted successfully'
