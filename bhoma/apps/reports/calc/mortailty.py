from bhoma.utils.mixins import UnicodeMixIn
from collections import defaultdict
from bhoma.utils.logging.utils import log_exception
from bhoma.apps.patient.encounters.config import get_display_name
import json
import uuid

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
    # The format is: xformkey: ["long display", "short disp."]
    "anaemia": ["Anaemia", "Anaemia"],
    "diarrhea": ["Diarrhea","Diarrhea"],
    "hiv_aids": ["HIV / AIDS","HIV/AIDS"],
    "infection": ["Infection","Infection"],
    "pregnancy": ["Pregnancy","Pregnancy"],
    "delivery_birth": ["Delivery / Birth","Dlvry/Birth"],
    "hypertension": ["Hypertension","Hypertnsn"],
    "measles": ["Measles","Measles"],
    "pneumonia": ["Pneumonia","Pneumonia"],
    "malaria": ["Malaria","Malaria"],
    "tb": ["TB","TB"],
    "stroke": ["Stroke","Stroke"],
    "heart_problem": ["Heart Problem","Heart"],
    "injuries": ["Injuries","Injuries"],
    "other": ["Other","Other"],
    "blank": ["Question Left Blank","Blank"],
    # child
    "still_birth": ["Still Birth","Stillborn"],
    "prolonged_labor": ["Prolonged Labor","Labor"],
    "malformed": ["Malformed at Birth","Malformed"],
    "premature": ["Prematurity", "Premature",],
    # place
    "home": ["Home","Home"],
    "health_facility": ["Clinic / Hospital","Clinic/Hospital"],
    # aggregates
    "num_adult_men": ["Males > 14", "Males > 14",],
    "num_adult_women": ["Females > 14", "Females > 14",],
    "num_under_five": ["Children < 5","Children < 5"],
    "num_five_up": ["Children 5-14", "Children 5-14"],
    "num_households": ["Number of Households", "Number of Households"],
    "": ["No Answer","?"]
    }

ADULT_MALE_CAUSE_OPTIONS = ["anaemia", "diarrhea", "hiv_aids", "infection", 
                            "hypertension", "measles", "pneumonia", 
                            "malaria", "tb", "stroke", "heart_problem", "injuries", 
                            "other", "blank", ""]

ADULT_FEMALE_CAUSE_OPTIONS = ["anaemia", "diarrhea", "hiv_aids", "infection", "pregnancy", 
                              "delivery_birth", "hypertension", "measles", "pneumonia", 
                              "malaria", "tb", "stroke", "heart_problem", "injuries", 
                              "other", "blank", ""]

CHILD_CAUSE_OPTIONS = ["still_birth", "prolonged_labor", "malformed", "premature", 
                 "infection", "diarrhea", "hiv_aids", "measles", "malaria", 
                 "pneumonia", "other", "blank", ""]


PLACE_OPTIONS = ["home", "health_facility", "other", "blank", ""]

AGGREGATE_OPTIONS = ["num_adult_men", "num_adult_women", 
                     "num_under_five", "num_five_up"]

class CauseOfDeathDisplay(UnicodeMixIn):
    
    def __init__(self, title, options):
        self.title = title
        self._options = options
        self._data = defaultdict(lambda: 0)
        self._uid = uuid.uuid4().hex
    
    def add_data(self, data):
        for key, val in data.items():
            self._data[key] += val
    
    @property
    def total(self):
        return sum(self._data.values())
    
    @property
    def uid(self):
        return self._uid
    
    def get_display_data(self):
        total = self.total
        if total==0:
            return [(DISPLAY_MAPPING[item][0], 0, 0) for item in self._options]
        else:
            return [(DISPLAY_MAPPING[item][0], self._data[item], \
                     float(self._data[item]) / float(self.total) * 100) \
                     for item in self._options]
    
    def get_flot_data(self):
        return json.dumps([{'bars': {'show': 'true'}, 'data': [[i, float(self._data[item]) / float(self.total) * 100]], 'label': DISPLAY_MAPPING[item][1]} for i, item in enumerate(self._options)])
        
    def get_flot_labels(self):
        return json.dumps([[float(i) + 0.5, DISPLAY_MAPPING[item][1] if i % 2 == 0 else "<br>%s" % DISPLAY_MAPPING[item][1]] for i, item in enumerate(self._options)])
        
    def __unicode__(self):
        return self.title
    