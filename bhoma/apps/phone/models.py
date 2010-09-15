from datetime import datetime
from couchdbkit.ext.django.schema import *

class SyncLog(Document):
    """
    A log of a single sync operation.
    """
    
    date = DateTimeProperty()
    chw_id = StringProperty()
    previous_log_id = StringProperty() # previous sync log, forming a chain
    last_seq = IntegerProperty() # the last_seq of couch during this sync
    
    def __unicode__(self):
        return "%s of %s on %s (%s)" % (self.operation, self.chw_id, self.date.date(), self._id)
