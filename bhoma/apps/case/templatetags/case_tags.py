import types
from datetime import date, datetime
from django import template
from bhoma.apps.xforms.util import value_for_display

register = template.Library()

@register.simple_tag
def format_case(case):
    template = '<span class="%(status)s">%(status)s: %(modifier)s</span>'
    status = "closed" if case.closed else "open"
    if case.closed:
        modifier = value_for_display(case.outcome) if case.outcome else "unknown outcome"
    else:
        modifier = value_for_display(case.status) if case.status else "unknown status"
    return template % {"status": status, "modifier": modifier}