#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import re
from django.db import models
from bhoma.apps.djangocouch.models import CouchModel
from django.db.models.signals import post_save
from bhoma.apps.djangocouch.signals import couch_post_save


# These models are couch models, but they aren't meant to synchronize across sites.
# This is primarily so that we can do location-based queries from within our couch
# application.
class LocationType(models.Model):
    """
    A type of location.
    """

    # django doesn't like to automatically pluralize things (and neither
    # do i), but it's not a _huge_ inconvenience to provide them both,
    # since the names of LocationTypes rarely change
    singular = models.CharField(max_length=100)
    plural   = models.CharField(max_length=100)

    slug = models.CharField(max_length=30, unique=True,
        help_text="An URL-safe alternative to the <em>plural</em> field.")
                  

    class Meta:
        verbose_name = "Type"


    def __unicode__(self):
        return self.singular

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)

    
class Point(models.Model):
    """
    This model represents an anonymous point on the globe. 
    """

    latitude  = models.DecimalField(max_digits=13, decimal_places=10)
    longitude = models.DecimalField(max_digits=13, decimal_places=10)


    def __unicode__(self):
        return "%s, %s" % (self.latitude, self.longitude)

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)


class Location(models.Model):
    """
    This model represents a named point on the globe. 
    """

    # use a data-based couch id so this synchronizes reasonably across forms
    # NOTE: will this break because of conflicting _rev numbers?
    # czue: removed since these live only in django
    # _id  = models.CharField(max_length=65, editable=False) # we use loc-<type.slug>-<slug> for a max of 65 chars
    
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=30, unique=True,
                            help_text="A unique identifier that will be lowercased "\
                                      "going into the database.")
    type = models.ForeignKey(LocationType)
    point = models.ForeignKey(Point, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)
    
    
    @property
    def path(self):
        next = self
        locations = []

        while next is not None:
            locations.insert(0, next)
            next = next.type.exists_in

        return locations

    @property
    def full_name(self):
        """
        Return the full-qualified name of this Location, including all
        of its ancestors. Ideal for displaying in the Django admin.
        """

        def _code(location):
            return location.slug or\
                ("#%d" % location.pk)

        return "/".join(map(_code, self.path))


    def save(self, *args, **kwargs):

        # remove any superfluous spaces from the _name_. it would be a
        # huge bother to require the user to do it manually, but the
        # __search__ method assumes that a single space is the only
        # delimiter, so we'll do it here transparently.
        self.name = re.sub(r"\s+", " ", self.name)

        # do some processing on the slug field to ensure we only store 
        # lowercase and strip spaces
        self.slug = self.slug.lower().strip()
        
        # generate our couchdb _id if it wasn't resent
        # czue: commented out since we are keeping these models out of couch
        #if not self._id:
        #    self._id = "loc-%s-%s" % (self.type.slug, self.slug)
        
        # then save the model as usual
        models.Model.save(self, *args, **kwargs)
        
