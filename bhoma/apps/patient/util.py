from django.http import HttpResponseForbidden
from bhoma.apps.locations.util import location_type

def restricted_patient_data(f):
    """decorator to restrict access to patient-identifiable data unless logged in
    as superuser or installed in a clinic setting"""
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser or location_type() == 'clinic':
            return f(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()
    return wrap
