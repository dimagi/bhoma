from bhoma.utils.mixins import UnicodeMixIn
import logging

class ReportDisplayValue(UnicodeMixIn):
    """
    Report Display Value (mirrors the javascript class)x
    """
    num = 0
    denom = 0
    slug = ""
    hidden = False
    display_name = ""
    
    def __init__(self, num, denom, slug, hidden, display_name):
        self.num = num
        self.denom = denom
        self.slug = slug
        self.hidden = hidden
        self.display_name = display_name if display_name is not None else self.slug
            
    
    def __unicode__(self):
        return "%s%s: %s (%s/%s) %s" % (self.display_name, 
                                     " (%s)" % self.slug if self.slug != self.display_name else "",
                                     self.indicator_percent, self.num, self.denom,
                                     "(hidden)" if self.hidden else "")
    @property
    def indicator_percent(self):
        if self.denom == 0:
            return "N/A"
        return "%.2f %%" % (float(self.num) / float(self.denom) * 100.0)
    
    @property
    def graph_value(self):
        if self.denom == 0:
            return 0
        return (float(self.num) / float(self.denom) * 100.0)
     
class ReportDisplayRow(UnicodeMixIn):
    """
    Report displays for a row of data
    """
    name = ""
    values = []
    clinic = ""
    year = None
    month = None
    _slug_to_values_map = {}
    
    def __init__(self, name, values, year, month, clinic):
        self.name = name
        self.values = values
        self.year = year
        self.month = month
        self.clinic = clinic
        self._slug_to_values_map = {}
    
    
    def __unicode__(self):
        return "%s (%s, %s, %s):\n%s" % (self.name, self.year, self.month, self.clinic, 
                                     "\n".join([str(val) for val in self.values]))
    
        
    def get_value(self, slug):
        """
        Get a value from the row by slug.
        """
        if slug in self._slug_to_values_map:
            return self._slug_to_values_map[slug]
        else:
            matched_vals = [val for val in self.values if val.slug == slug]
            if len(matched_vals) == 1:
                self._slug_to_values_map[slug] = matched_vals[0]    
                return matched_vals[0]
            else:
                logging.error("%s matches found for %s in %s! Expected only one." % \
                              (len(matched_vals), slug, self))
                return None

    @classmethod
    def from_view_results(cls, view_results_row):
        """
        Build a report display row from a couchdb object
        """
        key = view_results_row["key"]
        value = view_results_row["value"]
        month, year = None, None
        if len(key) > 2:
            year, js_month, clinic = key[:3]
            month = js_month + 1
        else:
            raise Exception("Need to fully specify key!")
        report_name = value["name"]
        report_values = value["values"]
        vals = []
        for rep_val in report_values:
            value_display = ReportDisplayValue(rep_val["num"], rep_val["denom"],
                                               rep_val["slug"], rep_val["hidden"],
                                               rep_val["display_name"])
            vals.append(value_display)
            
        return ReportDisplayRow(report_name, vals, year, month, clinic)

class ReportDisplay(UnicodeMixIn):
    """
    The whole report
    """
    
    name = ""
    rows = []
    def __init__(self, name, rows):
        self.name = name
        self.rows = rows 
        
    @classmethod
    def from_view_results(cls, results):
        """
        Build a report display row from a couchdb object
        """
        report_name = ""
        display_rows = []
        for row in results:
            row_display = ReportDisplayRow.from_view_results(row)
            display_rows.append(row_display)
            # these are assumed to always be the same so just pick one
            report_name = row_display.name
        return ReportDisplay(report_name, display_rows)
        