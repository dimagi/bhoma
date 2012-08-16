from dimagi.utils.mixins import UnicodeMixIn
import logging
from django.utils.datastructures import SortedDict
from bhoma.apps.reports import const
from bhoma.apps.locations.util import clinic_display
from django.core.urlresolvers import reverse
import itertools

REPORT_TYPES = (("f", "fractional"), ("n", "numeric"))

class NoDataException(Exception): pass
    

class ReportDisplayValue(UnicodeMixIn):
    """
    Report Display Value 
    """
    
    slug = ""
    hidden = False
    display_name = ""
    description = ""
    
    def __init__(self, slug, hidden, display_name, description):
        self.slug = slug
        self.hidden = hidden
        self.display_name = display_name
        self.description = description
        
    def __unicode__(self):
        return "%s%s: %s %s" % (self.display_name, 
                                " (%s)" % self.slug if self.slug != self.display_name else "",
                                self.tabular_display, "(hidden)" if self.hidden else "")
    @property
    def tabular_display(self):
        """How this appears in tables"""
        # subclasses should override this
        pass
    
    @property
    def graph_value(self):
        """How this appears in graphs"""
        # subclasses should override this
        pass
        

class NumericalDisplayValue(ReportDisplayValue):
    """
    Report Display Value for numeric fields 
    """
    value = 0

    def __init__(self, value, slug, hidden, display_name, description):
        super(NumericalDisplayValue, self).__init__(slug, hidden, display_name, description)
        self.value = value
            
    
    @property
    def tabular_display(self):
        return str(self.value)
    
    @property
    def graph_value(self):
        return self.value
     
    

class FractionalDisplayValue(ReportDisplayValue):
    """
    Fractional Report Display Value (mirrors the javascript class used in the PI reports)
    """
    num = 0
    denom = 0
    
    def __init__(self, num, denom, slug, hidden, display_name, description):
        super(FractionalDisplayValue, self).__init__(slug, hidden, display_name, description)
        self.num = num
        self.denom = denom
            
    
    @property
    def tabular_display(self):
        if self.denom == 0:
            return "N/A"
        return "%.0f%%  (%s/%s)" % ((float(self.num) / float(self.denom) * 100.0), self.num, self.denom) 
    
    @property
    def graph_value(self):
        if self.denom == 0:
            return "N/A"
        return int(float(self.num) / float(self.denom) * 100.0)
    
    def __unicode__(self):
        return "%s%s: %s (%s/%s) %s" % (self.display_name, 
                                     " (%s)" % self.slug if self.slug != self.display_name else "",
                                     self.tabular_display, self.num, self.denom,
                                     "(hidden)" if self.hidden else "")
     

class ReportDisplayRow(UnicodeMixIn):
    """
    Report displays for a row of data
    """
    name = ""
    values = []
    keys = {}
    _slug_to_values_map = {}
    
    def __init__(self, name, keys, values):
        self.name = name
        self.values = values
        self.keys = keys
        self._slug_to_values_map = {}
    
    
    def __unicode__(self):
        return "%s (%s):\n%s" % (self.name, ", ".join(["%s:%s" %(key,val) for key, val in self.keys.items()]), 
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
            elif len(matched_vals) > 1:
                logging.error("%s matches found for %s in %s! Expected at most one." % \
                              (len(matched_vals), slug, self))
                return None
        
    def get_link(self, slug):
        return None

class PIReportDisplayRow(ReportDisplayRow):
    
    def __init__(self, report_slug, name, keys, values):
        super(PIReportDisplayRow, self).__init__(name, keys, values)
        self.report_slug = report_slug
        if "Clinic" in self.keys:
            self.clinic_code = self.keys["Clinic"]
            self.keys["Clinic"] = clinic_display(self.clinic_code)    
        else:
            self.clinic_code = None
            
    def get_link(self, slug):
        if self.clinic_code is not None and "Year" in self.keys and "Month" in self.keys:
            details_url_base = reverse("pi_details")
            return "%(url)s?year=%(year)s&month=%(month)s&clinic=%(clinic)s&report=%(report)s&col=%(col)s" % \
                    {"url": details_url_base, "year": self.keys["Year"],
                     "month": self.keys["Month"], "clinic": self.clinic_code,
                     "report": self.report_slug, "col": slug} 

    
        return None
    
class CHWPIReportDisplayRow(ReportDisplayRow):
    
    def __init__(self, chw_id, name, keys, values):
        super(CHWPIReportDisplayRow, self).__init__(name, keys, values)
        self.chw_id = chw_id
            
    def get_link(self, slug):
        if self.chw_id is not None and "Year" in self.keys and "Month" in self.keys:
            details_url_base = reverse("chw_pi_details")
            return "%(url)s?year=%(year)s&month=%(month)s&chw=%(chw)s&col=%(col)s" % \
                    {"url": details_url_base, "year": self.keys["Year"],
                     "month": self.keys["Month"], "chw": self.chw_id,
                     "col": slug} 

        return None
    
class ReportDisplay(UnicodeMixIn):
    """
    The whole report
    """
    
    name = ""
    rows = []
    
    def __init__(self, name, rows):
        self.name = name
        self.rows = rows 
        
    def _get_representative_values(self):
        vals = {}
        for row in self.rows:
            for val in row.values :
                if not val.hidden and val.slug not in vals:
                    vals[val.slug] = val
        return vals.values()
    
    def get_slug_keys(self):
        return [val.slug for val in sorted(self._get_representative_values(), key=lambda val: val.slug)]
        
    def get_display_value_keys(self):
        return [val.display_name for val in sorted(self._get_representative_values(), key=lambda val: val.slug)]
        
    def get_descriptions(self):
        return [val.description for val in sorted(self._get_representative_values(), key=lambda val: val.slug)]
    
    def has_data(self):
        return hasattr(self, "rows") and len(self.rows) > 0
    
    def get_data(self, include_urls=True):
        if not self.has_data():
            raise NoDataException
        else: 
            baseline_row = self.rows[0]
    
        ordered_keys = [key for key in baseline_row.keys]
        ordered_value_keys = self.get_slug_keys()
        headings = list(itertools.chain([key for key in baseline_row.keys],
                                        self.get_display_value_keys()))
        display_rows = []
        
        for row in self.rows:
            ordered_values = [row.get_value(key).tabular_display \
                              if row.get_value(key) else "N/A" \
                              for key in ordered_value_keys ]
            display_values = list(itertools.chain([row.keys[key] for key in ordered_keys], 
                                                  ordered_values))
            if include_urls:
                links = list(itertools.chain([None for key in ordered_keys],
                                             [row.get_link(key) for key in ordered_value_keys ]))
                display_rows.append([(display_values[i], links[i]) for i in range(len(display_values))])
            else:
                display_rows.append([display_values[i] for i in range(len(display_values))])
        return {"headings": headings, "rows": display_rows}
        
class PIReport(ReportDisplay):
    
    def __init__(self, slug, rows):
        self.name = const.get_name(slug)
        self.rows = rows 
        self.slug = slug
        
    @classmethod
    def from_pi_view_results(cls, report_slug, results):
        """
        Build a report display row from a couchdb view results object
        """
        
        def _get_rowkey(row):
            # the part of the row that is used as an index: year, month, clinic
            return tuple(row["key"][:3])
        
        def _get_rowval(row):
            # convert the row to a report display value
            col_slug = row["key"][3]
            return FractionalDisplayValue(row["value"][0], row["value"][1],
                                          col_slug, const.is_hidden(report_slug, col_slug),
                                          const.get_display_name(report_slug, col_slug), 
                                          const.get_description(report_slug, col_slug))
        
        def _get_displaykeys(rowkey):
            keys = SortedDict()
            keys["Clinic"] = rowkey[2]
            keys["Year"] = rowkey[0]
            keys["Month"] = rowkey[1] + 1 # have to convert js date
            return keys
        
        # iterate through results, bucketing into groups
        all_data = {}
        for row in results:
            rowkey = _get_rowkey(row)
            if rowkey in all_data:
                all_data[rowkey].append(_get_rowval(row))
            else:
                all_data[rowkey]=[_get_rowval(row)]
            
        report_name = const.get_name(report_slug)
        all_rows = []
        for rowkey, vals in all_data.items():
            all_rows.append(PIReportDisplayRow(report_slug, report_name, _get_displaykeys(rowkey), vals))
        
        return PIReport(report_slug, all_rows)
        