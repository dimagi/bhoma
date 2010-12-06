"""
This script syncs data from a satellite clinic server to the national server,
based on the settings.
"""

from django.core.management.base import LabelCommand, CommandError
from django.conf import settings
from bhoma.utils.couch.sync import pull_from_national_to_local,\
    push_from_local_to_national
from bhoma.utils.parsing import string_to_boolean

BOTH = "both"
PUSH = "push"
PULL = "pull"
SYNC_DIRECTIONS = (BOTH, PUSH, PULL)

class Command(LabelCommand):
    help = "Syncs data between a clinic and central server"
    args = "<direction> <continuous> <cancel>"
    label = 'Direction of sync (options are both, pull, and push; default is both)'\
            'continuous (true / false; default is false)' \
            'cancel (true / false; default is false)'
     
    def handle(self, *args, **options):
        direction = BOTH if len(args) < 1 else args[0].strip().lower()
        if not direction in SYNC_DIRECTIONS:
            raise CommandError('"%s" is not a valid sync direction.  It must be one of %s' % \
                               (direction,
                                ", ".join(('"%s"' % dir for dir in SYNC_DIRECTIONS))))

        continuous = False if len(args) < 2 else string_to_boolean(args[1].strip())
        cancel = False if len(args) < 3 else string_to_boolean(args[1].strip())
        do_sync(direction, continuous, cancel)
                
    def __del__(self):
        pass
    
def do_sync(direction, continuous, cancel):
    push = direction in (BOTH, PUSH)
    pull = direction in (BOTH, PULL)
    # todo implement cancel
    if push:
        print "pushing local changes to server (continuous=%s)" % continuous
        push_from_local_to_national(continuous)
    if pull:
        print "pulling down new data from server (continuous=%s)" % continuous
        pull_from_national_to_local(continuous)
        
