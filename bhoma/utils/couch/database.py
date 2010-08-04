from bhoma.apps.patient.models import CPatient

def get_db():
    """
    Get the bhoma database.  
    """
    # this is a bit of a hack, since it assumes all the models talk to the same
    # db.  that said a lot of our code relies on that assumption.
    return CPatient.get_db()