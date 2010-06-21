"""
This script syncs data from a satellite clinic server to the national server,
based on the settings.
"""

from django.core.management.base import LabelCommand, CommandError
from django.conf import settings
from bhoma.utils.couch.sync import pull_from_national_to_clinic,\
    push_from_clinic_to_national

BOTH = "both"
PUSH = "push"
PULL = "pull"
SYNC_DIRECTIONS = (BOTH, PUSH, PULL)

class Command(LabelCommand):
    help = "Syncs data between a clinic and central server"
    args = "<direction>"
    label = 'Direction of sync (options are both, pull, and push; default is both)'
     
    def handle(self, *args, **options):
        direction = BOTH if len(args) < 1 else args[0].strip().lower()
        if not direction in SYNC_DIRECTIONS:
            raise CommandError('"%s" is not a valid sync direction.  It must be one of %s' % \
                               (direction,
                                ", ".join(('"%s"' % dir for dir in SYNC_DIRECTIONS))))
        
        do_sync(direction)
                
    def __del__(self):
        pass
    
def do_sync(direction):
    push = direction in (BOTH, PUSH)
    pull = direction in (BOTH, PULL)
    if pull:
        print "pulling down new data from server"  
        pull_from_national_to_clinic()
    if push:
        print "pushing local changes to server"  
        push_from_clinic_to_national()
        