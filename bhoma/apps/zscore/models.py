#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models


# These models are couch models, but they aren't meant to synchronize across sites.
# This is primarily so that we can do location-based queries from within our couch
# application.

    
class Zscore(models.Model):
    """
    Zscore list for underfive reporting
    """
    GENDER_CHOICES = (
        (u'm', u'Male'),
        (u'f', u'Female'),
    )

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.IntegerField(max_length=2)
    l_value = models.FloatField(max_length = 10)
    m_value = models.FloatField(max_length = 10)
    s_value = models.FloatField(max_length = 10)
    sd_three_neg = models.FloatField(max_length=4)
    sd_two_neg = models.FloatField(max_length=4)
    sd_one_neg = models.FloatField(max_length=4)
    sd_zero = models.FloatField(max_length=4)
    
    def __unicode__(self):
        name_to_return = "Gender: %s; Age in Months; %s;" \
            %(self.gender, self.age)
        return name_to_return
