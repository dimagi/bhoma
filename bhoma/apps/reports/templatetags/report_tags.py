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
def render_user(user):
    """
    A short display for a user object
    """
    if not user:
        return "<td>UNKNOWN USER</td><td>N/A</td><td>N/A</td>"
    else:
        if user.get("doc_type", "") == "CommunityHealthWorker":
            return "<td>%s</td><td>%s</td><td>%s</td>" % (user["username"], user["current_clinic_id"], "CHW") 
        elif "#user" in user:
            user_rec = user["#user"]
            return "<td>%s</td><td>%s</td><td>%s</td>" % (user_rec["username"], user["clinic_id"], "CSW") 
    return "<td>UNKNOWN USER TYPE</td><td>N/A</td><td>N/A</td>"
    
@register.simple_tag
def render_report(report):
    """
    Convert a ReportDisplay object into a displayable report.  This is a big
    hunk of template tagging.
    """
    if len(report.rows) == 0:
        return "<h3>Sorry, there's no data for the report and parameters you selected.  " \
               "Try running the report over a different range.</h3>"
    else: 
        baseline_row = report.rows[0]
    
    ordered_keys = [key for key in baseline_row.keys]
    ordered_value_keys = report.get_slug_keys()
    
    
    headings = list(itertools.chain([key for key in baseline_row.keys],
                                    report.get_display_value_keys()))
    display_rows = []
    for row in report.rows:
        ordered_values = [row.get_value(key).tabular_display if row.get_value(key) else "N/A" for key in ordered_value_keys ]
        display_values = list(itertools.chain([row.keys[key] for key in ordered_keys], 
                                              ordered_values))
        display_rows.append(display_values)
    return render_to_string("reports/partials/couch_report_partial.html", 
                            {"headings": headings, "rows": display_rows})

@register.simple_tag
def render_summary_graph(report):
    """
    Generate a graph that plots all the pi indicators for each clinic
    from the data in the ReportDisplay object
    """
    
    if len(report.rows) == 0:
        return
       
    """Create array of all indicator data by month for each clinic"""
    headings = report.get_display_value_keys()
    report_data = []
    for row in report.rows:
        i=1
        display_row = []
        ordered_values = [row.get_value(key).graph_value if row.get_value(key) else 0 for key in headings ]
        for value in ordered_values:
            display_row.append([value, i])
            i+=1
        row_with_clinic = list(itertools.chain([row.keys['Clinic']], [row.keys['Month']], display_row))
        report_data.append(row_with_clinic)
    
    """sort by clinic, remove clinic name and month, combine data for same clinic"""    
    sorted_data=sorted(report_data, key=lambda data: data[0])
    clinic_list=[]
    display_data=[]
    num_entries = len(ordered_values)
    for entry in sorted_data:
        if entry[0] not in clinic_list:
            clinic_list.append(entry[0])
            display_data.append(entry[2:])
        else:
            display_data[-1] = display_data[-1] + entry[2:]
         
    """Size height of plot based on number of indicators (~50 px per Indicator)"""
    height_per_indicator = 50
    height_plot = num_entries*height_per_indicator + height_per_indicator
    
    return render_to_string("reports/partials/report_summary_graph.html", 
                    {"headings": json.dumps(headings), 
                     "rows": display_data, 
                     "height": height_plot, 
                     "clinic_names": clinic_list
                     })

@register.simple_tag
def render_graph(report):
    """
    Generate a graph from the data in the ReportDisplay object
    """
    
    if len(report.rows) == 0:
        return
    else: 
        baseline_row = report.rows[0]
    
    ordered_keys = [key for key in baseline_row.keys]
    descriptions = report.get_descriptions()
    keys = report.get_slug_keys()
    
    display_data = []
    display_label = []
    for key in keys:
        indicator_values = []
        i=1
        for row in report.rows:
            data_value = [row.get_value(key).graph_value if row.get_value(key) else 0]
            for value in data_value:
                indicator_values.append([value, i])
                i+=1
        display_data.append([indicator_values])
    
    for row in report.rows:
        label = (list(itertools.chain([row.keys[key] for key in ordered_keys])))
        display_label.append(label)
         
    """Size height of plot based on number of rows (~50 px per value)"""
    height_per_value = 50
    height_plot = len(report.rows)*height_per_value + height_per_value

    return render_to_string("reports/partials/report_graph.html", 
                    {"labels": json.dumps(display_label), 
                     "descriptions": descriptions, 
                     "titles": keys, 
                     "display_data": display_data, 
                     "height": height_plot
                     })


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
    
