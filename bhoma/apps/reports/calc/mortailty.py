from bhoma.utils.mixins import UnicodeMixIn


class MortalityGroup(UnicodeMixIn):
    
    def __init__(self, clinic, agegroup, gender):
        self.clinic = clinic
        self.agegroup = agegroup
        self.gender = gender
    
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