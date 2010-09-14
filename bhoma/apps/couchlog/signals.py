from django.core.signals import got_request_exception
from django.conf import settings
from bhoma.utils.logging.signals import exception_logged

def log_request_exception(sender, request, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_request_exception(request)
    # bolt on the clinic code too
    record.clinic_id = settings.BHOMA_CLINIC_ID
    record.save()
    
def log_standard_exception(sender, exc_info, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_exc_info(exc_info)
    # bolt on the clinic code too
    record.clinic_id = settings.BHOMA_CLINIC_ID
    record.save()
    
    
exception_logged.connect(log_standard_exception)
got_request_exception.connect(log_request_exception)