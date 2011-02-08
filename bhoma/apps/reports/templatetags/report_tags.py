from datetime import datetime, timedelta
from django import template
import itertools
from django.template.loader import render_to_string
import json
from bhoma.apps.locations.models import Location
from django.utils.datastructures import SortedDict
from bhoma.apps.reports.calc.mortailty import CauseOfDeathDisplay, \
    PLACE_OPTIONS, CHILD_CAUSE_OPTIONS, ADULT_CAUSE_OPTIONS

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
def render_user_inline(user, ):
    """
    A short display for a user object
    """
    if user:
        if user.get("doc_type", "") == "CommunityHealthWorker":
            return "%s (%s)" % (user["username"], "CHW") 
        elif "#user" in user:
            user_rec = user["#user"]
            return "%s (%s)" % (user_rec["username"], "CSW") 
    return "UNKNOWN USER"
    
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
def render_report(report, template="reports/partials/couch_report_partial.html"):
    """
    Convert a ReportDisplay object into a displayable report.  This is a big
    hunk of template tagging.
    """
    if report is None or not hasattr(report, "rows") or len(report.rows) == 0:
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
        ordered_values = [row.get_value(key).tabular_display if row.get_value(key) else "0" for key in ordered_value_keys ]
        display_values = list(itertools.chain([row.keys[key] for key in ordered_keys], 
                                              ordered_values))
        display_rows.append(display_values)
    return render_to_string(template, 
                            {"headings": headings, "rows": display_rows})

@register.simple_tag
def render_summary_graph(report):
    """
    Generate a graph that plots all the pi indicators for each clinic
    from the data in the ReportDisplay object
    """
    
    if report is None or len(report.rows) == 0:
        return
       
    """Create array of all indicator data by month for each clinic"""
    headings = report.get_display_value_keys()
    report_data = []
    for row in report.rows:
        ordered_values = [row.get_value(key).graph_value if row.get_value(key) else 0 for key in headings ]
        row_with_clinic = list(itertools.chain([row.keys['Clinic']], [str(row.keys['Month'])], [str(row.keys['Year'])], [ordered_values]))
        report_data.append(row_with_clinic)

    """sort by clinic"""    
    sorted_data=sorted(report_data, key=lambda data: data[0])

    """create a clinic list, date list for display on plot, combine data for same clinic"""
    clinic_list=[]
    date_list=[]
    data_by_clinic=[]
    for entry in sorted_data:
        if entry[0] not in clinic_list:
            clinic_list.append(entry[0])
            date_list.append([str(entry[1] + "/" + entry[2])])
            data_by_clinic.append(entry[3:])
        else:
            data_by_clinic[-1] = data_by_clinic[-1] + entry[3:]
            date_list[-1] = date_list[-1] + [str(entry[1] + "/" + entry[2])]
    
    """go through data for each clinic, add y-axis point for plotting based on number of months plotted for each clinic"""
    """check that data value valid, create list with data values that don't exist for plotting"""
    height_per_indicator = 50
    num_indicators = len(ordered_values)
    plot_height =[]
    display_data = []
    valid_data = []
    for row in data_by_clinic:
        display_row = []
        valid_row = []
        increment_val = len(row) + 1
        y_value = 1
        indicator_counter = 0
        month_counter = 0
        for month in row:
            display_month = []
            valid_value = []
            for x_value in month:
                if x_value != "N/A":
                    data_value = x_value
                    valid = "True"
                else:
                    data_value = 0
                    valid = "False"
                    
                display_month.append([data_value, y_value])
                valid_value.append(valid)
                
                if indicator_counter < (num_indicators-1):
                    y_value += increment_val
                    indicator_counter += 1
                else:
                    """reset condition"""
                    month_counter += 1
                    y_value = month_counter+1
                    indicator_counter = 0
                    
            display_row.append(display_month)     
            valid_row.append(valid_value)    
        display_data.append(display_row)
        valid_data.append(valid_row)
        plot_height.append(len(row)*num_indicators*height_per_indicator + height_per_indicator)
                
    """add clinic name"""
    clinic_name_list=[]
    for clinic in clinic_list:
        try:
            clinic_obj = Location.objects.get(slug=clinic)
            clinic = "%s (%s)" % (clinic_obj.name, clinic_obj.slug)
        except Location.DoesNotExist:
            pass
        clinic_name_list.append(clinic)
    
    descriptions = report.get_descriptions()
    keys = report.get_slug_keys()
    
    return render_to_string("reports/partials/report_summary_graph.html", 
                    {"headings": json.dumps(headings), 
                     "rows": display_data, 
                     "height": plot_height, 
                     "clinic_names": clinic_name_list,
                     "dates": date_list,
                     "descriptions": descriptions, 
                     "titles": keys,
                     "valid_data": valid_data
                     })

@register.simple_tag
def render_graph(report):
    """
    Generate a graph from the data in the ReportDisplay object
    !! removed from use 08/10/10 mjt - for now...
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
    
@register.simple_tag
def render_mortality_report(report, type):
    """
    Convert a Mortality Report object into a displayable report.  This is a big
    hunk of template tagging.
    """
    if report is None or len(report.groups) == 0:
        return "<h3>Sorry, there's no data for the report and parameters you selected.  " \
               "Try running the report over a different range.</h3>"
    
    if type == "cause":
        female_data = CauseOfDeathDisplay("Females > 14 who died", ADULT_CAUSE_OPTIONS)
        male_data = CauseOfDeathDisplay("Males > 14 who died", ADULT_CAUSE_OPTIONS)
        child_data = CauseOfDeathDisplay("Children < 14 who died", CHILD_CAUSE_OPTIONS)
        title = "Causes of death" 
    elif type == "place":
        female_data = CauseOfDeathDisplay("Females > 14 who died", PLACE_OPTIONS)
        male_data = CauseOfDeathDisplay("Males > 14 who died", PLACE_OPTIONS)
        child_data = CauseOfDeathDisplay("Children < 14 who died", PLACE_OPTIONS)
        title = "Places of death" 
    else:
        raise Exception("Invalid mortality type: %s, valid options are 'place' and 'cause'" % type)
    for group in report.groups:
        if group.is_adult() and group.is_female():
            female_data.add_data(report.get_data(group))
        elif group.is_adult() and group.is_male():
            male_data.add_data(report.get_data(group))
        elif group.is_child():
            child_data.add_data(report.get_data(group))
    
    return render_to_string("reports/partials/mortality_cause_of_death_partial.html", 
                            {"title": title,
                             "adult_male_data": male_data,
                             "adult_female_data": female_data,
                             "child_data": child_data})

