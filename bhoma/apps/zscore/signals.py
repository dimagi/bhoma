from math import pow
from bhoma.apps.xforms.signals import xform_saved
from couchdbkit.resource import ResourceNotFound
from bhoma.utils.logging import log_exception
from bhoma.utils.couch.database import get_db


def insert_zscores(sender, form, **kwargs):
    """For Under5, hook up zscore calculated"""
    from bhoma.apps.zscore.models import Zscore
    from bhoma.apps.patient.models import CPatient
    
    patient_id = form.xpath("case/patient_id")
    
    if not patient_id or not get_db().doc_exist(patient_id):  
        return
    
    patient = CPatient.get(patient_id)
    if form["#type"] == "underfive" and patient.age_in_months <= 60:
        
        form.zscore_calc_good = []
        try:
            zscore = Zscore.objects.get(gender=patient.gender, age=patient.age_in_months)
        except Zscore.DoesNotExist:
            # how is this possible?
            zscore = None
            
        if zscore and form.xpath("nutrition/weight_for_age") and form.xpath("vitals/weight"):
            def calculate_zscore(l_value,m_value,s_value,x_value):
                #for L != 0, Z = (((X/M)^L)-1)/(L*S)
                eval_power = pow((float(x_value) / m_value),l_value)
                return ((eval_power - 1) / (l_value * s_value))
            
            def compare_sd(zscore_value):
                if zscore_value >= 0: 
                    return "0"
                elif 0 > zscore_value and zscore_value >= -2: 
                    return "-2"
                elif -2 > zscore_value and zscore_value >= -3: 
                    return "-3"
                elif -3 > zscore_value:
                    return "below -3"
            
            zscore_num = calculate_zscore(zscore.l_value, zscore.m_value, zscore.s_value, form["vitals"]["weight"])
            sd_num = compare_sd(zscore_num)
            
            if form.xpath("nutrition/weight_for_age") == sd_num:
                form.zscore_calc_good = "true"
            else:
                form.zscore_calc_good = "false"
        
        else:
            form.zscore_calc_good = "unable_to_calc"
        
        form.save()
    

xform_saved.connect(insert_zscores)