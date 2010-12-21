from bhoma.utils.parsing import string_to_datetime
from datetime import datetime, timedelta

'''
Pregnancy logic goes here.
'''
from bhoma.apps.patient.encounters import config

GESTATION_LENGTH = 40 * 7 # in days

def is_healthy_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace == config.HEALTHY_PREGNANCY_NAMESPACE

def is_sick_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace == config.SICK_PREGNANCY_NAMESPACE

def is_pregnancy_encounter(encounter):
    return encounter.get_xform().namespace in [config.HEALTHY_PREGNANCY_NAMESPACE, 
                                               config.SICK_PREGNANCY_NAMESPACE,
                                               config.DELIVERY_NAMESPACE]

def first_visit_data(form):
    return form.xpath("first_visit")
    
def lmp_from_edd(edd):
    return edd - timedelta(days=GESTATION_LENGTH)

def edd_from_lmp(lmp):
    return lmp + timedelta(days=GESTATION_LENGTH)

def edd_from_gestational_age(visit_date, gest_age):
    return visit_date + timedelta(days=(GESTATION_LENGTH - 7*gest_age))
 
def get_edd(encounter):
    """
    Get an edd from the form.  First checks the lmp field, then the edd field,
    then the gestational age.  If none are filled in returns nothing.  Otherwise
    calculates the edd from what it finds.
    """
    formdoc = encounter.get_xform()
    if (formdoc.xpath("first_visit/lmp")):
        # edd = lmp + 40 weeks = 280 days
        return edd_from_lmp(string_to_datetime(formdoc.xpath("first_visit/lmp")).date())
    elif (formdoc.xpath("first_visit/edd")):
        return string_to_datetime(formdoc.xpath("first_visit/edd")).date()
    elif (formdoc.xpath("gestational_age")):
        # edd = visit date + 280 days - (gestational age * 7) days
        return edd_from_gestational_age(encounter.visit_date, int(formdoc.xpath("gestational_age"))) 
    else:
        # fall back
        return None    
    
def get_pregnancy_outcome(form):
    """
    If this case has a pregnancy outcome, return it
    """
    # TODO
    # if the form is a delivery form or a sick pregnancy form that 
    # closes the pregnancy case then get that outcome. 
    return None