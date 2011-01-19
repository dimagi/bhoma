from fabric.api import *
from fab.config import *
from datetime import datetime

'''
OS Commands
'''

def create_directory(dir):
    sudo("mkdir -p %(dir)s" % {"dir" : dir})

def backup_directory(src, target):
    sudo("cp -Rp %(src)s %(target)s" % {"src": src, "target": target})

def move_directory(src, target):
    sudo("mv %(src)s %(target)s" % {"src": src, "target": target})

def remove_directory(target):
    sudo("rm -R %(target)s" % {"target": target})

def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H.%m.%S.%f")

def restore_directory(src, target):
    tmpdir = PATH_SEP.join((TMP_DIR, timestamp_string()))
    move_directory(target, tmpdir)
    backup_directory(src, target)
    remove_directory(src)

