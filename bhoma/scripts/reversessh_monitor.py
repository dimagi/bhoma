import os
import logging
import logging.handlers

remotes = {
    7100: 'chongwe-district',
    7200: 'kafue-district',
    7300: 'luangwa-district',
    7111: 'chalimbana-clinic',
    7114: 'kampekete-clinic',
    7122: 'ngwerere-clinic',
    7215: 'chipapa-clinic',
    7218: 'kafue-mission-clinic',
    7392: 'mandombe-clinic',
}

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
    ]

    response = os.popen('ssh nobody@localhost -p %d -o "BatchMode yes" -o "ConnectTimeout %d" 2>&1' % (port, TIMEOUT)).read().lower()

    if any((phrase in response) for phrase in up_phrases):
        return True
    elif any((phrase in response) for phrase in down_phrases):
        return False
    else:
        raise RuntimeError('don\'t recognize ssh response [%s]' % response)

def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=2**20, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
    root.addHandler(handler)
init_logging()

if __name__ == '__main__':

    for port, site in remotes.iteritems():
        try:
            up = make_contact(port)
            logging.info('%s [%d] is %s' % (site, port, 'up' if up else 'down'))
        except:
            logging.exception('unexpected error')
