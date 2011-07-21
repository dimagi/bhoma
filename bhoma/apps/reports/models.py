from couchdbkit.ext.django.schema import *
from dimagi.utils.mixins import UnicodeMixIn
from couchversion.models import AppVersionedDocument


class PregnancyReportRecord(AppVersionedDocument, UnicodeMixIn):
    """
    Document representing a pregnancy in couchdb
    """
    patient_id = StringProperty(required=True)
    clinic_id = StringProperty(required=True) # we assume one clinic per pregnancy
    id = StringProperty(required=True)
    lmp = DateProperty()
    edd = DateProperty()
    visits = IntegerProperty(required=True)
    start_date = DateProperty(required=True)
    first_visit_date = DateProperty(required=True)
    
    # report values
    ever_tested_positive = BooleanProperty()
    first_date_tested_positive = DateProperty()
    not_on_haart_when_test_positive = BooleanProperty()
    got_nvp_when_tested_positive = BooleanProperty()
    not_on_haart_when_test_positive_ga_14 = BooleanProperty()
    had_two_healthy_visits_after_pos_test_ga_14 = BooleanProperty()
    got_azt_when_tested_positive = BooleanProperty()
    got_azt_haart_on_consecutive_visits = BooleanProperty()
    tested_positive_rpr = BooleanProperty()
    tested_positive_rpr_and_had_later_visit = BooleanProperty()
    got_penicillin_when_rpr_positive = BooleanProperty()
    partner_got_penicillin_when_rpr_positive = BooleanProperty()
    got_three_doses_fansidar = BooleanProperty()
    eligible_three_doses_fansidar = BooleanProperty()
    dates_preeclamp_treated = ListProperty()
    dates_preeclamp_not_treated = ListProperty()
    
    def __unicode__(self):
        return "%s, Pregnancy: %s (due: %s)" % (self.patient_id, self.id, self.edd)
    
    
import bhoma.apps.reports.signals