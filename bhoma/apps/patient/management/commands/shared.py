"""Code that is shared by the management commands"""
import logging
from bhoma.utils.couch.database import get_db

def log_and_abort(level, msg):
    """
    Logs a message, and if the the threshold is > DEBUG also prints to console.
    This method is called log_and_abort because it is often used to log a reason
    for breaking out of a _changes feed.,
    """
    logging.log(level, msg)
    if level > logging.DEBUG:
        print msg
    

def is_old_rev(change):
    """Is a document on an older rev"""
    if change.rev:
        return get_db().get_rev(change.id) != change.rev
    # we don't know if we don't know the rev, so don't make any assumptions
    return False

def is_deleted(doc_id):
    """Has a document been deleted?"""
    return not get_db().doc_exist(doc_id)