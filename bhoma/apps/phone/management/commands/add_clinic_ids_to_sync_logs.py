from django.core.management.base import LabelCommand, CommandError
from bhoma.apps.phone.models import SyncLog
from bhoma.apps.chw.models import CommunityHealthWorker
from couchdbkit.exceptions import ResourceNotFound

class Command(LabelCommand):
    help = "One time script to add missing clinic ids to sync logs so they sync back to clinic servers"
    args = "version"
    label = ""
    
    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage: manage.py add_clinic_ids_to_sync_logs')
        
        for sl in SyncLog.view("phone/sync_logs_by_chw", reduce=False, 
                                include_docs=True):
            try:
                chw = CommunityHealthWorker.get(sl.chw_id)
            except ResourceNotFound:
                chw = None
            if not chw:
                print "failed to update %s" % sl
                continue
            sl.clinic_id = chw.current_clinic_id
            sl.save()
                        