#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from .models import *

class DrugAdmin(admin.ModelAdmin):
    pass
    list_display = ("name", "types_display", "formulations_display")
    list_filter = ("name",)
    
admin.site.register(DrugType)
admin.site.register(DrugFormulation)
admin.site.register(Drug, DrugAdmin)
