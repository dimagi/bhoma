from django.contrib import admin
from bhoma.apps.phone.models import SyncLog

class SyncAdmin(admin.ModelAdmin):
    list_display = ("date", "operation", "phone_id", "chw_id", "last_seq")
    list_filter = ("date", "operation", "phone_id", "chw_id")
    
admin.site.register(SyncLog, SyncAdmin)