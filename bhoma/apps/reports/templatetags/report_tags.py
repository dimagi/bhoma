from datetime import datetime, timedelta
from django import template
import itertools
from django.template.loader import render_to_string
import json

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

@register.simple_tag
def render_graph(report):
    """
    Generate a graph from the data in the ReportDisplay object
    """
    
    if len(report.rows) == 0:
       return
    else: 
        baseline_row = report.rows[0]
    
    headings = [val.display_name for val in baseline_row.values if not val.hidden]
    display_rows = []
#    for row in report.rows:
#        ordered_values = [row.get_value(key).indicator_percent for key in ordered_value_keys]
#        display_values = list(itertools.chain([row.clinic, row.year, int_to_month(row.month)], 
#                                              ordered_values))
#        display_rows.append(display_values)
    display_rows = []
    num_rows = 2
    for i in range(1,num_rows+1):
        display_values = [[50,1], [55,2], [60,3], [55,4], [50,5]]
        display_rows.append(display_values)
    
    display_rows.append([[60,1], [65,2], [70,3], [80,4], [100,5]])
    display_rows.append([[60,1], [65,2], [70,3], [80,4], [100,5]])
            
    headings = ["QI1", "QI2", "QI3", "QI4", "QI5"]
    
    """Size height of plot based on number of indicators (~50 px per Indicator)"""
    height_per_indicator = 50
    height_plot = len(display_values)*height_per_indicator + height_per_indicator
    
    return render_to_string("reports/partials/report_graph.html", 
                    {"headings": headings, "rows": display_rows, "height": height_plot})

        
    #Put data into format to plot
    #Figure out what to do about multiple months, choose what to display
#    data1 = [[50, 1], [55, 3], [68, 5], [94, 7]]
#    data2 = [[55, 2], [60, 4], [75, 6], [100, 8]]
    
#    return render_to_string("reports/partials/report_graph.html", 
#                            {"series": json.dumps(data1)},
#                            {"series": json.dumps(data1)})


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
    
