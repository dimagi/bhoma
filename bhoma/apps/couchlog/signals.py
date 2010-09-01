from django.core.signals import got_request_exception
from django.conf import settings

def handle_exception(sender, request, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_request_exception(request)
    # bolt on the clinic code too
    record.clinic_id = settings.BHOMA_CLINIC_ID
    record.save()
    
    

got_request_exception.connect(handle_exception)