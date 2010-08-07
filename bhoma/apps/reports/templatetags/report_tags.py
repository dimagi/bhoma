from datetime import datetime, timedelta
from django import template
import itertools
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def int_to_month(month_number):
    # there has to be a better way to do this
    d = datetime(2010, month_number, 1)
    return d.strftime("%b")
    
@register.simple_tag
def js_int_to_month(month_number):
    """
    Convert a javascript integer to a month name.  Javascript months are 0
    indexed."""
    return int_to_month(month_number + 1)
    
@register.simple_tag
def render_report(report):
    """
    Convert a ReportDisplay object into a displayable report.  This is a big
    hunk of template tagging.
    """
    if len(report.rows) == 0:
        return "<h3>Sorry, there's no data for the report and parameters you selected.  Try running the report over a different range.</h3>"
    else: 
        baseline_row = report.rows[0]
    
    ordered_value_keys = [val.display_name for val in baseline_row.values if not val.hidden]
    headings = list(itertools.chain(["Clinic", "Year", "Month"], ordered_value_keys))
    display_rows = []
    for row in report.rows:
        ordered_values = [row.get_value(key).indicator_percent for key in ordered_value_keys]
        display_values = list(itertools.chain([row.clinic, row.year, int_to_month(row.month)], 
                                              ordered_values))
        display_rows.append(display_values)
    return render_to_string("reports/partials/couch_report_partial.html", 
                            {"headings": headings, "rows": display_rows})

@register.filter
def dict_lookup(dict, key):
    '''Get an item from a dictionary.'''
    return dict.get(key)
    
@register.filter
def array_lookup(array, index):
    '''Get an item from an array.'''
    if index < len(array):
        return array[index]
    
@register.filter
def attribute_lookup(obj, attr):
    '''Get an attribute from an object.'''
    if (hasattr(obj, attr)):
        return getattr(obj, attr)
    
