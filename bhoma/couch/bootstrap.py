from couchdbkit import *
from couchdbkit.loaders import FileSystemDocsLoader
from .models import District, Clinic, Patient

def bootstrap(dbname="patient", delete_db=False):
    """Bootstraps the database for couch"""
    # server object
    server = Server()
    
    if delete_db:
        try:    server.delete_db(dbname)
        except: pass

    # get or create database
    db = server.get_or_create_db("patient")

    # load design doc
    loader = FileSystemDocsLoader("./_design")
    loader.sync(db, verbose=True)
    
    # associate objects to the db
    District.set_db(db)
    Clinic.set_db(db)
    Patient.set_db(db)
