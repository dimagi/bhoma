from couchdbkit.ext.django.schema import *


class CPregnancy(Document):
    """
    Document representing a pregnancy in couchdb
    """
    patient_id = StringProperty(required=True)
    id = StringProperty(required=True)
    lmp = DateProperty(required=True)
    edd = DateProperty(required=True)
    visits = IntegerProperty(required=True)
    first_visit_date = DateProperty(required=True)
    
    # report values
    ever_tested_positive = BooleanProperty()
    got_nvp_when_tested_positive = BooleanProperty()
    hiv_test_done = BooleanProperty()
    
    def __unicode__(self):
        return "%s, Pregnancy: %s (due: %s)" % (self.patient.formatted_name, self.id, self.edd)
    
    
    