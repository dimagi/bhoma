#!/usr/bin/env python
from django.core.management import execute_manager
import sys, os
# use a default settings module if none was specified on the command line

# add some directories to the path
filedir = os.path.dirname(__file__)
contrib_root = os.path.join(filedir, "contrib")
sys.path.append(contrib_root)

touchforms_root = os.path.join(filedir, 'submodules', 'touchforms')
sys.path.append(touchforms_root)

######################
# hack!  local restkit and couchdbkit for debugging
pathhack = False
if pathhack:
    sourcedir = os.path.join(filedir, "..", "..")
    restkitdir = os.path.join(sourcedir, "couchdb", "restkit")
    couchdbkitdir = os.path.join(sourcedir, "couchdb", "couchdbkit")
    sys.path.append(restkitdir)
    sys.path.append(couchdbkitdir)
######################

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
