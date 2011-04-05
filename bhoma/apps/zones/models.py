from __future__ import absolute_import
from couchdbkit.ext.django.schema import *
from dimagi.utils.mixins import UnicodeMixIn

class ClinicZone(Document, UnicodeMixIn):
    """
    A Zone in a clinic
    """
    clinic_id = StringProperty(required=True)
    zone = IntegerProperty(required=True)
    households = IntegerProperty()
    
    def __unicode__(self):
        return "Clinic %s Zone %s" % (self.clinic_id, self.zone)


