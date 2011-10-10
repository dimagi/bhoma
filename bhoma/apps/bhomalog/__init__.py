from django.utils.html import escape
from bhoma.apps.locations.util import clinic_display_name
def wrapper(error):
    
    def truncate(message, length=100, append="..."):
        if length < len(append):
            raise Exception("Can't truncate to less than %s characters!" % len(append))
        return "%s%s" % (message[:length], append) if len(message) > length else message
     
    def format_type(type):
        return escape(type)
    
    clinic_code = error.clinic_id if "clinic_id" in error else None
    clinic_display = "%s (%s)" % (clinic_display_name(clinic_code), clinic_code)\
                         if clinic_code else "UNKNOWN"
    return [error.get_id,
            error.archived, 
            clinic_display,
            error.date.strftime('%Y-%m-%d %H:%M:%S') if error.date else "", 
            format_type(error.type), 
            truncate(error.message), 
            error.url,
            "archive",
            "email"]
    