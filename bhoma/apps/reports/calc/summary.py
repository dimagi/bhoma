from dimagi.utils.couch.database import get_db
from bhoma.apps.reports.display import NumericalDisplayValue, ReportDisplayRow,\
    ReportDisplay
from bhoma.apps.patient.encounters.config import get_display_name
from bhoma.apps.locations.models import Location

def get_clinic_summary(group_level=2):
    results = get_db().view("xforms/counts_by_type", group=True, group_level=group_level).all() 
                            
    report_name = "Clinic Summary Report (number of forms filled in by type)"
    clinic_map = {}
    
    for row in results:
        key = row["key"]
        value = row["value"]
        namespace, clinic = key[:2]
        # hackity hack, don't show device reports
        if namespace == "http://code.javarosa.org/devicereport":
            continue
        if not clinic in clinic_map:
            clinic_map[clinic] = []
        value_display = NumericalDisplayValue(value,namespace, hidden=False,
                                              display_name=get_display_name(namespace), description="")
        clinic_map[clinic].append(value_display)
    
    all_clinic_rows = []
    for clinic, rows in clinic_map.items():
        try:
            clinic_obj = Location.objects.get(slug=clinic)
            clinic = "%s (%s)" % (clinic_obj.name, clinic_obj.slug)
        except Location.DoesNotExist:
            pass
        all_clinic_rows.append(ReportDisplayRow(report_name, {"clinic": clinic},rows))
    return ReportDisplay(report_name, all_clinic_rows)
    