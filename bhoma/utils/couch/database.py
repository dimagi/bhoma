
def get_db():
    """
    Get the bhoma database.  
    """
    # this is a bit of a hack, since it assumes all the models talk to the same
    # db.  that said a lot of our code relies on that assumption.
    # this import is here because of annoying dependencies
    from bhoma.apps.patient.models import CPatient
    return CPatient.get_db()