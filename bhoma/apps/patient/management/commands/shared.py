"""Code that is shared by the management commands"""
import logging

def log_and_abort(level, msg):
    """
    Logs a message, and if the the threshold is > DEBUG also prints to console.
    This method is called log_and_abort because it is often used to log a reason
    for breaking out of a _changes feed.,
    """
    logging.log(level, msg)
    if level > logging.DEBUG:
        print msg
    
