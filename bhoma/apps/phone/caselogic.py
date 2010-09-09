"""
Logic about chws phones and cases go here.
"""
from bhoma.apps.case.models.couch import PatientCase

def meets_sending_criteria(case, synclog):
    """
    Whether this case should be sent out.
    """
    # if never before synced, always include this
    if not synclog: return True
    # otherwise only sync something that's been modified since the date of the log
    return case.modified_on > synclog.date
    
def cases_for_chw(chw):
    """
    From chw clinic zone, get the list of open cases
    """
    key = [chw.current_clinic_id, chw.current_clinic_zone]
    return PatientCase.view_with_patient("case/open_for_chw", key=key).all()

def cases_for_patient(patient_id):
    """
    Get the list of open cases for a particular patient
    """
    print PatientCase.view_with_patient("case/open_for_patient", key=patient_id).all()
    return PatientCase.view_with_patient("case/open_for_patient", key=patient_id).all()
