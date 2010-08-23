"""
Drug utility methods.
"""
from bhoma.apps.drugs.models.couch import CDrugRecord

def extract_prescriptions(xform):
    return [CDrugRecord.wrap(dict) for dict in xform.xpath("drugs_prescribed")]
    
def drug_type_prescribed(xform, type):
    for drug in extract_prescriptions(xform): 
        if type in drug.types:  return True
    return False
            
        
    