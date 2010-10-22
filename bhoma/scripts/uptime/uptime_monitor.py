#!/usr/bin/python

import sys
import urllib2
import logging
import json
from gmailloghandler import TLSSMTPHandler

RECIPIENTS = [
    'bhoma@dimagi.com',
]

def get_email_credentials():
    try:
        from localemailsettings import SMTP_USER, SMTP_PASS
        return (SMTP_USER, SMTP_PASS)
    except ImportError:
        raise Exception("It doesn't look like you configured email logging!")
    
def init_logging():
    try: 
        un, pw = get_email_credentials()
    except Exception:
        logging.error("No localemailsettings file found.  Email notifications will not be sent")
        return 
        
    root = logging.getLogger()
    root.setLevel(logging.ERROR)
    handler = TLSSMTPHandler(
        ('smtp.gmail.com', 587),
        'Uptime Monitor <%s>' % un,
        RECIPIENTS,
        'BHOMA Server Error',
        (un, pw)
    )
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
    root.addHandler(handler)


def main(args):
    if len(args) < 1:
        print "You must pass in a url to monitor!"
        sys.exit()
    init_logging()
    url = args[0]
    try:
        f = urllib2.urlopen(url, timeout=180)
        data = json.loads(f.read())
        errors = data['errors']
        if errors:
            logging.error('errors on server:\n\n' + '\n'.join(errors))
            print 'errors on server:\n\n' + '\n'.join(errors)
            return 1
        return 0
    except Exception, e:
        print 'could not contact server: %s (%s %s)' % (url, type(e), str(e))
        logging.error('could not contact server: %s (%s %s)' % (url, type(e), str(e)))
        return 1
    


if __name__ == "__main__":
    main(sys.argv[1:])