from __future__ import absolute_import
from couchdbkit.ext.django.schema import *
    
"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.
"""

class CDrugRecord(Document):
    """
    Record of a drug, prescription or dispensation
    """
    name = StringProperty()
    types = ListProperty()
    formulations = ListProperty()
    
    class Meta:
        app_label = 'drugs'
