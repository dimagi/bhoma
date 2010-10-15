import sys, os
import tempfile
from datetime import datetime
from subprocess import Popen, PIPE, call

SUCCESS = 0

def simulate_failure():
    return 1

def git_fetch():
    GIT_FETCH_COMMAND = "git fetch origin master"
    proc = Popen(GIT_FETCH_COMMAND)
    return proc.wait()

def git_merge():
    GIT_MERGE_COMMAND = "git merge origin"
    proc = Popen(GIT_MERGE_COMMAND)
    return proc.wait()

def backup_directory(src, target):
    CP_COMMAND = "cp -Rp %(src)s %(target)s"
    print "copying %(src)s to %(target)s" % {"src": src, "target": target}
    proc = Popen(CP_COMMAND % {"src": src, "target": target})
    return proc.wait()

def move_directory(src, target):
    MV_COMMAND = "mv -Rp %(src)s %(target)s"
    print "moving %(src)s to %(target)s" % {"src": src, "target": target}
    proc = Popen(MV_COMMAND % {"src": src, "target": target})
    return proc.wait()

def remove_directory(target):
    RM_COMMAND = "rm -R %(target)s"
    print "removing %(target)s" % {"target": target}
    proc = Popen(RM_COMMAND % {"target": target})
    return proc.wait()

def timestamp_string():
    return str(datetime.now())

def restore_directory(src, target):
    tmpdir = os.path.join(tempfile.gettempdir(), timestamp_string())
    status = move_directory(target, tmpdir)
    if status:
        return status
    status = backup_directory(src, target)
    if status:
        return status
    return remove_directory(src)
    