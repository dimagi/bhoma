import os
import logging
import logging.handlers
from reversessh_tally import REMOTE_CLINICS

TIMEOUT = 90
LOG_FILE = '/var/log/bhoma/reversessh.log'

def make_contact(port):
    up_phrases = [
        'host key verification failed',
        'permission denied',
    ]
    down_phrases = [
        'connection timed out',
        'connection refused',
        'connection closed by',
    ]

    response = os.popen('ssh nobody@localhost -p %d -o "BatchMode yes" -o "ConnectTimeout %d" 2>&1' % (port, TIMEOUT)).read().lower()

    if any((phrase in response) for phrase in up_phrases):
        return True
    elif any((phrase in response) for phrase in down_phrases):
        return False
    else:
        raise RuntimeError('don\'t recognize ssh response [%s]' % response)

def site_port(site_id):
    site_id = str(site_id)
    a = site_id[2]
    b = site_id[4:6]
    return int('7' + a + (b if b else '00'))

def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=2**20, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
    root.addHandler(handler)
init_logging()

if __name__ == '__main__':

    for site_id in sorted(REMOTE_CLINICS.keys()):
        site = REMOTE_CLINICS[site_id]
        port = site_port(site_id)
        try:
            up = make_contact(port)
            logging.info('%s [%d / %d] is %s' % (site, site_id, port, 'up' if up else 'down'))
        except:
            logging.exception('%s: unexpected error' % site)
