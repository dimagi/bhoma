from django.core.signals import got_request_exception

def handle_exception(sender, request, **kwargs):
    from bhoma.apps.couchlog.models import ExceptionRecord
    record = ExceptionRecord.from_request_exception(request)
    
    

got_request_exception.connect(handle_exception)