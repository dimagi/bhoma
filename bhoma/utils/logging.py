from __future__ import absolute_import
import sys
import traceback
import logging

def log_exception(e):
    """Log an exception, with a stacktrace"""
    type, value, tb = sys.exc_info()
    traceback_string = '\n'.join(traceback.format_tb(tb))
    logging.error(e)
    logging.error(traceback_string)