from django.conf import settings
from couchlog.signals import couchlog_created

def add_bhoma_extras(record, **kwargs):
    # bolt on the clinic code and app version, as well as our extra_info
    record.clinic_id = settings.BHOMA_CLINIC_ID if not settings.BHOMA_IS_DHMT \
                       else "%sDHMT" % settings.BHOMA_CLINIC_ID
    record.commit_id = settings.BHOMA_COMMIT_ID
    # poor man's AppVersionedDoc
    record.app_version = settings.APP_VERSION
    record.original_app_version = settings.APP_VERSION
    record.save()
    
couchlog_created.connect(add_bhoma_extras) 
