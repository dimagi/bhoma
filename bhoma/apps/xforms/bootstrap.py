import os
import logging
import hashlib
from django.db import transaction
from django.conf import settings
from bhoma.apps.xforms.models.django import XForm

def bootstrap():
    try:
        # create xform objects for everything in the configured directory,
        # if we don't already have them
        files = os.listdir(settings.XFORMS_BOOTSTRAP_PATH)
        logging.debug("bootstrapping forms in %s" % settings.XFORMS_BOOTSTRAP_PATH)
        for filename in files:
            # is this sneaky lazy loading a reasonable idea?
            full_name = os.path.join(settings.XFORMS_BOOTSTRAP_PATH, filename)
            file = open(full_name, "r")
            try:
                checksum = hashlib.sha1(file.read()).hexdigest()
                file.close()
                if XForm.objects.filter(checksum=checksum).count() > 0:
                    logging.debug("skipping %s, already loaded" % filename)
                else:
                    xform = XForm.from_file(full_name)
                    logging.debug("created: %s from %s" % (xform, filename))
            except IOError, e:
                logging.error("Problem loading file: %s. %s" % (filename, e))
            except Exception, e:
                logging.exception("Unknown problem bootstrapping file: %s." % filename)
            finally:
                file.close()
            
    except Exception, e:
        transaction.rollback_unless_managed()
        logging.error(("Problem bootstrapping xforms: %s.  Ignoring.  If the " \
                       "application seems broken, this is probably why") % e)
        
        return
        
