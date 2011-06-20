from bhoma.apps.webapp.config import get_current_site
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from bhoma.apps.webapp.touchscreen.options import TouchscreenOptions

def aggregation_required(aggregation_levels):
    """
    Require the application to be in a certain aggregation level
    in order for certain views to work.
    """
    # if they pass in a string, use it, othewise assume a list 
    if isinstance(aggregation_levels, basestring):
        aggregation_levels = [aggregation_levels]
    
    def decorator (view_func):
        def wrapped_view(request, *args, **kwargs):
            site = get_current_site()
            if site.type.slug in aggregation_levels:
                return view_func(request, *args, **kwargs)
            else:
                return render_to_response("bad_permissions.html", {"options": TouchscreenOptions.default()},
                                          context_instance = RequestContext(request))
                
        return wrapped_view
    return decorator