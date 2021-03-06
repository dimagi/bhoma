#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import absolute_import
import re
from django.db import models
from djangocouch.models import CouchModel
from django.db.models.signals import post_save
from djangocouch.signals import couch_post_save


# These models are couch models, but they aren't meant to synchronize across sites.
# This is primarily so that we can do location-based queries from within our couch
# application.
class DrugType(models.Model):

    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'drugs'

    def __unicode__(self):
        return self.name
    
class DrugFormulation(models.Model):
    
    name = models.CharField(max_length=100)            

    class Meta:
        app_label = 'drugs'
        
    def __unicode__(self):
        return self.name
    
class Drug(models.Model):
    """
    This model represents the bhoma essential drug list. 
    """
    
    name = models.CharField(max_length=150)
    types = models.ManyToManyField(DrugType)
    formulations = models.ManyToManyField(DrugFormulation)
    
    slug = models.CharField(max_length=30, unique=True,
                            help_text="A unique identifier that will be lowercased "\
                                      "going into the database.")
    
    class Meta:
        app_label = 'drugs'
    
    def __unicode__(self):
        return self.name
    
    def types_display(self):
        return ", ".join([str(type) for type in self.types.all()])
    
    def formulations_display(self):
        return ", ".join([str(type) for type in self.formulations.all()])