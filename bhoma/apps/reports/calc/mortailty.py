from bhoma.utils.mixins import UnicodeMixIn
from collections import defaultdict
from bhoma.utils.logging.utils import log_exception

class MortalityGroup(UnicodeMixIn):
    
    def __init__(self, clinic, agegroup, gender):
        self.clinic = clinic
        self.agegroup = agegroup
        self.gender = gender
    
    def is_adult(self):
        return self.agegroup == "adult"
    
    def is_child(self):
        return self.agegroup == "child"
    
    def is_male(self):
        return self.gender == "m"
    
    def is_female(self):
        return self.gender == "f"
    
    
    def unique_string(self):
        """A unique string to identify this"""
        # This must be unique as in - if any of the values change it should change
        return str(self)
    
    def __unicode__(self):
        return "%s, %s, %s" %(self.clinic, self.agegroup, self.gender)
    
    def __eq__(self, other):
        return self.clinic == other.clinic \
               and self.agegroup == other.agegroup \
               and self.gender == other.gender
               
class MortalityReport(UnicodeMixIn):
    
    def __init__(self):
        self._clinic_map = {}
    
    def add_data(self, group, type, count):
        if not self.has_group(group):
            self._clinic_map[group.unique_string()] = \
                {"group": group, "values": defaultdict(lambda: 0)}
                            
        self._clinic_map[group.unique_string()]["values"][type] += count
    
    @property
    def groups(self):
        return [val["group"] for key, val in self._clinic_map.items()]
    
    @property
    def group_data(self):
        return dict([(grp, self._clinic_map[grp]["values"]) for grp in self._clinic_map])
        
    def has_group(self, group):
        return group.unique_string() in self._clinic_map
    
    def get_data(self, group):
        if self.has_group(group):
            return self._clinic_map[group.unique_string()]["values"]
    
    def __unicode__(self):
        return "mortality report: %s groups" % len(self._clinic_map)
    
DISPLAY_MAPPING = {
    "anaemia": "Anaemia",
    "diarrhea": "Diarrhea",
    "hiv_aids": "HIV / AIDS",
    "infection": "Infection",
    "pregnancy": "Pregnancy",
    "delivery_birth": "Delivery / Birth",
    "hypertension": "Hypertension",
    "measles": "Measles",
    "pneumonia": "Pneumonia",
    "malaria": "Malaria",
    "tb": "TB",
    "stroke": "Stroke",
    "heart_problem": "Heart Problem",
    "injuries": "Injuries",
    "other": "Other",
    "blank": "Question Left Blank",
    "still_birth": "Still Birth",
    "prolonged_labor": "Prolonged Labor",
    "malformed": "Malformed at Birth",
    "premature": "Prematurity", 
    "": "No Answer"}

ADULT_OPTIONS = ["anaemia", "diarrhea", "hiv_aids", "infection", "pregnancy", 
                 "delivery_birth", "hypertension", "measles", "pneumonia", 
                 "malaria", "tb", "stroke", "heart_problem", "injuries", 
                 "other", "blank", ""]

CHILD_OPTIONS = ["still_birth", "prolonged_labor", "malformed", "premature", 
                 "infection", "diarrhea", "hiv_aids", "measles", "malaria", 
                 "pneumonia", "other", "blank", ""]


class CauseOfDeathDisplay(UnicodeMixIn):
    
    def __init__(self, title, options):
        self.title = title
        self._data = defaultdict(lambda: 0)
    
    def add_data(self, data):
        for key, val in data.items():
            self._data[key] += val
    
    @property
    def total(self):
        return sum(self._data.values())
    
    def get_display_data(self):
        return [(DISPLAY_MAPPING[item], self._data[item], \
                 float(self._data[item]) / float(self.total) * 100) \
                 for item in DISPLAY_MAPPING]
            
    def __unicode__(self):
        return self.title
    