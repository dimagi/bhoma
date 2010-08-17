from __future__ import absolute_import

from datetime import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import *
from bhoma.apps.encounter.models import Encounter
from couchdbkit.schema.properties_proxy import SchemaListProperty
from bhoma.apps.case.models.couch import PatientCase
from bhoma.apps.patient.mixins import CouchCopyableMixin


"""
Couch models.  For now, we prefix them starting with C in order to 
differentiate them from their (to be removed) django counterparts.
"""

# these two currently aren't used for anything.
# though they might be necessary to be used during district sync
class CDistrict(Document):
    slug = StringProperty()
    name = StringProperty()
    
    class Meta:
        app_label = 'patient'

class CClinic(Document):
    slug = StringProperty()
    name = StringProperty()
    district_id = StringProperty()
    
    class Meta:
        app_label = 'patient'


class CPhone(Document):
    is_default = BooleanProperty()
    number = StringProperty()
    device_id = StringProperty()
    created = DateTimeProperty()
    
    class Meta:
        app_label = 'patient'

class CAddress(Document):
    """
    An address.
    """
    zone = IntegerProperty()
    village = StringProperty()
    clinic_id = StringProperty()
    
    class Meta:
        app_label = 'patient'

class ReportContribution(Document):
    """
    Dynamically generated data describing how a patient contributes to a certain
    report.
    """
    date = DateProperty(required=True)
    clinic_id = StringProperty(required=True)
    dynamic_data =  DictProperty()

    class Meta:
        app_label = 'patient'

class CPatient(Document, CouchCopyableMixin):
    first_name = StringProperty(required=True)
    middle_name = StringProperty()
    last_name = StringProperty(required=True)
    birthdate = DateProperty(required=True)
    birthdate_estimated = BooleanProperty()
    gender = StringProperty(required=True)
    patient_id = StringProperty()
    clinic_ids = StringListProperty()
    address = SchemaProperty(CAddress)
    encounters = SchemaListProperty(Encounter)
    phones = SchemaListProperty(CPhone)
    cases = SchemaListProperty(PatientCase)
    
    # this field stores dynamic data, and is blown away and recalculated upon patient save
    report_data = SchemaListProperty(ReportContribution)
        
    class Meta:
        app_label = 'patient'

    def __unicode__(self):
        return "%s %s (%s, DOB: %s)" % (self.first_name, self.last_name,
                                        self.gender, self.birthdate)
    @property
    def formatted_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    @property
    def age(self):
        if not self.birthdate:
            return None
        return int((datetime.now().date() - self.birthdate).days / 365.2425)
    
    @property
    def age_in_months(self):
        if not self.birthdate:
            return None
        ttl_days = int((datetime.now().date() - self.birthdate).days)
        return int(round(ttl_days / 365.2425 * 12))
            
    @property
    def formatted_age(self):
        if not self.birthdate:
            return None
        return format_age((datetime.now().date() - self.birthdate).days)
                
    @property
    def default_phone(self):
        if len(self.phones) > 0:
            defaults = [phone for phone in self.phones if phone.is_default]
            if len(defaults) > 0: return defaults[0].number
            return self.phones[0].number
        
        return None
    
    @property
    def formatted_id(self):
        if len(self.patient_id) != 12:
            return self.patient_id
        return '%s-%s-%s-%s' % (self.patient_id[:3], self.patient_id[3:6], 
                                self.patient_id[6:11], self.patient_id[11])
    
    def update_cases(self, case_list):
        """
        Update cases attached to a patient instance, or add
        them if they are new
        """
        for touched_case in case_list:
            found_index = len(self.cases)
            for i in range(len(self.cases)):
                pat_case = self.cases[i]
                if pat_case._id == touched_case._id:
                    found_index = i
            # replace existing cases with the same id if we find them
            # this defaults to appending on the end of the list
            self.cases[found_index] = touched_case
        
def format_age (ttl_days):
    def pl (base, n):
        return base + ('s' if n != 1 else '')
    def scount (n, base):
        return '%d %s' % (n, pl(base, n))

    days_per_year = 365.2425
    days_per_month = days_per_year / 12

    if ttl_days <= 0:
        return 'newborn'
    elif ttl_days <= 10:
        return scount(ttl_days, 'day')

    weeks = ttl_days / 7
    days = ttl_days % 7

    if weeks < 3:
        return '%s, %s' % (scount(weeks, 'wk'), scount(days, 'day'))
    elif weeks <= 8:
        return scount(weeks, 'wk')
    
    months = int(ttl_days / days_per_month)

    if months <= 18:
        return scount(months, 'mo')

    years = int(ttl_days / days_per_year)
    months = int(ttl_days / days_per_month) % 12

    if years < 3:
        return '%s, %s' % (scount(years, 'yr'), scount(months, 'mo'))
    else:
        return str(years)


