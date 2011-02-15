from subprocess import PIPE, Popen
from django.conf import settings
import os
import threading
import time
import logging

def shutdown(delay=0.):
    """
    Shutdown the system after a specified delay. Return immediately.
    """
    threading.Thread(target=do_shutdown, args=(delay,)).start()

def do_shutdown(delay):
    logging.warn('shutting down server in %d seconds...' % delay)
    time.sleep(delay)

    logging.warn('shutting down...')
    command = os.path.join(settings.BHOMA_ROOT_DIR, "scripts", "shutdown", "shutdown-wrapper") 
    p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    (out, err) = p.communicate()

    #if we've reached here, shutdown didn't work!
    logging.error('failed to shut down: %s' % str((out, err)))
