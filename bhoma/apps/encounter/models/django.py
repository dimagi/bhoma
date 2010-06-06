from __future__ import absolute_import

from django.db import models
from bhoma.apps.xforms.models import XForm

"""
Django models go here.  
"""

class EncounterType(models.Model):
    """
    A type of encounter.  These are linked to XForms which define the fields
    that are collected.
    """
    
    name = models.CharField(max_length=255)
    xform = models.ForeignKey(XForm)
    
    class Meta:
        app_label = 'encounter'

    def __unicode__(self):
        return self.name