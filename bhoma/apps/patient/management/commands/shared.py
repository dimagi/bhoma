"""Code that is shared by the management commands"""
import logging
from dimagi.utils.couch.database import get_db
from couchdbkit.resource import ResourceNotFound
from dimagi.utils.parsing import string_to_boolean

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
        try:
            return get_db().get_rev(change.id) != change.rev
        except ResourceNotFound:
            # this doc has been deleted.  clearly an old rev
            return True
    # we don't know if we don't know the rev, so don't make any assumptions
    return False

def are_you_sure(prompt="Are you sure you want to proceed? (yes or no): "):
    """
    Ask a user if they are sure before doing something.  Return
    whether or not they are sure
    """
    should_proceed = raw_input(prompt)
    try:
        return string_to_boolean(should_proceed)
    except Exception:
        return False

