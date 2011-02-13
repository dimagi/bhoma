from django.core.signals import got_request_exception
from django.conf import settings
#from dimagi.utils.logging.signals import exception_logged

def log_request_exception(sender, request, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_request_exception(request)
    _add_bhoma_extras(record, **kwargs)
    record.save()
    
def log_standard_exception(sender, exc_info, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_exc_info(exc_info)
    _add_bhoma_extras(record, **kwargs)
    record.save()

def _add_bhoma_extras(record, **kwargs):
    # bolt on the clinic code and app version, as well as our extra_info
    record.clinic_id = settings.BHOMA_CLINIC_ID
    record.commit_id = settings.BHOMA_COMMIT_ID
    if "extra_info" in kwargs:
        record.extra_info = kwargs["extra_info"]
    
    
#exception_logged.connect(log_standard_exception)
got_request_exception.connect(log_request_exception)