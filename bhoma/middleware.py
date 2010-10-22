import logging

from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext


class LogExceptionsMiddleware(object):
    """
    Simple middleware to log Django exceptions through Python's standard
    logging module.
    """
    
    def process_exception(self, request, exception):
        logger = logging.getLogger('bhoma.middleware.LogExceptions')
        logger.exception(exception)


class LoginRequiredMiddleware(object):
    """
    Makes login required for all views except those that start with the matched
    URLs.
    """
    
    urls = ['/accounts/login/', '/accounts/logout/', 
            '/accounts/login_ts/', '/accounts/logout_ts/',
            '/api/auth/', '/api/usernames/', "/api/diagnostics/",
            '/phone/', settings.MEDIA_URL]
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        for url in self.urls:
            if request.get_full_path().startswith(url):
                return # allow normal processing to continue
            
        return login_required(view_func)(request, *view_args, **view_kwargs)

class ConfigurationCheckMiddleware(object):
    """
    Makes login required for all views except those that start with the matched
    URLs.
    """
    def process_request(self, request):
        
        from bhoma.apps.locations.models import Location
        if request.get_full_path().startswith(settings.MEDIA_URL):
            return # allow normal processing to continue
        try:
            Location.objects.get(slug__iexact=settings.BHOMA_CLINIC_ID)
        except Location.DoesNotExist: 
            return render_to_response("bad_configuration.html",
                                      {"clinic_code": settings.BHOMA_CLINIC_ID},
                                      RequestContext(request))
        
