from datetime import datetime
from django.db import models
from bhoma.apps.djangocouch.models import CouchModel

# these are arbitrary
SYNC_OPERATIONS = (
    ("ir", "Initial Restore"),
    ("cs", "Case Synchronization"),
)

class SyncLog(CouchModel):
    """
    A log of a single sync operation.
    """
    
    date = models.DateTimeField(default=datetime.utcnow)
    operation = models.CharField(max_length=10, choices=SYNC_OPERATIONS)
    phone_id = models.CharField(max_length=40)
    chw_id = models.CharField(max_length=40)
    
    def __unicode__(self):
        return "%s of %s on %s" % (self.get_operation_display(), self.chw_id, self.date.date())
    