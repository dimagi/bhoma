from django.core.management.base import BaseCommand
from couchdbkit.client import Database
from collections import defaultdict
from django.conf import settings
from bhoma.apps.chw.models import CommunityHealthWorker


class Command(BaseCommand):
    """
    Run locally to generate stats for a CHW
    """
    def handle(self, *args, **options):
        db = Database(settings.BHOMA_NATIONAL_DATABASE)
        results = db.view("chw/by_clinic", include_docs=True).all()
        
        chws = [CommunityHealthWorker.wrap(res['doc']) for res in results]
        map = defaultdict(lambda: 0)
        
        def _fmt_date(dt):
            return "%s-%s" % (dt.year, dt.month)
        
        for chw in chws:
            print chw.username, chw.created_on
            map[_fmt_date(chw.created_on)] = map[_fmt_date(chw.created_on)] + 1
            
        for k in sorted(map.keys()):
            print "%s, %s" % (k, map[k])