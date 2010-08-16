#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from .models import *

class ZscoreAdmin(admin.ModelAdmin):
    list_display = ("gender", "age", "l_value", "m_value", "s_value", "sd_three_neg", "sd_two_neg", "sd_one_neg", "sd_zero")
    

admin.site.register(Zscore, ZscoreAdmin)

