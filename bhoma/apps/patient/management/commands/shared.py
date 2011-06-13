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
    

