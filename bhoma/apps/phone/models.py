from datetime import datetime
from django.db import models
from bhoma.apps.djangocouch.models import CouchModel

# these are arbitrary
SYNC_OPERATIONS = (
    ("ir", "Initial Restore"),
    ("cu", "Case Update"),
)

class SyncLog(CouchModel):
    """
    A log of a single sync operation.
    """
    # it's a couch model, but it doesn't sync.  we use the couch id as the restore_id
    
    date = models.DateTimeField(default=datetime.utcnow)
    operation = models.CharField(max_length=10, choices=SYNC_OPERATIONS)
    phone_id = models.CharField(max_length=40)
    chw_id = models.CharField(max_length=40)
    # the last_seq of couch during this sync
    last_seq = models.IntegerField(default=0) 
    
    def __unicode__(self):
        return "%s of %s on %s (%s)" % (self.get_operation_display(), self.chw_id, self.date.date(), self._id)


