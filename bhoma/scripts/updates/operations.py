import sys, os
import tempfile
from datetime import datetime
from subprocess import Popen, PIPE, call

SUCCESS = 0

def noop():
    pass

def verify_status(status, msg, callback_fail=sys.exit, callback_success=noop):
    if status != SUCCESS:
        print "%s FAILED" % msg
        callback_fail()
    else:
        print "%s SUCCESS" % msg
        callback_success()

                            
def simulate_failure():
    return 1

def _push_pop_dir(directory, command):
    return "cd %(dir)s && %(cmd)s && cd -" % {"dir": directory, "cmd" : command}

def git_fetch(directory=None):
    GIT_FETCH_COMMAND = "git fetch origin master"
    if directory:
        GIT_FETCH_COMMAND = _push_pop_dir(directory, GIT_FETCH_COMMAND)
    proc = Popen(GIT_FETCH_COMMAND, stderr=PIPE, stdout=PIPE, shell=True)
    return proc.wait()

def git_merge(directory=None):
    GIT_MERGE_COMMAND = "git merge origin"
    if directory:
        GIT_MERGE_COMMAND = _push_pop_dir(directory, GIT_MERGE_COMMAND)
    proc = Popen(GIT_MERGE_COMMAND, stderr=PIPE, stdout=PIPE, shell=True)
    return proc.wait()

def backup_directory(src, target):
    CP_COMMAND = "cp -Rp %(src)s %(target)s"
    print "copying %(src)s to %(target)s" % {"src": src, "target": target}
    proc = Popen(CP_COMMAND % {"src": src, "target": target}, stderr=PIPE, stdout=PIPE, shell=True)
    return proc.wait()

def move_directory(src, target):
    MV_COMMAND = "mv %(src)s %(target)s"
    print "moving %(src)s to %(target)s" % {"src": src, "target": target}
    proc = Popen(MV_COMMAND % {"src": src, "target": target}, stderr=PIPE, stdout=PIPE, shell=True)
    return proc.wait()

def remove_directory(target):
    RM_COMMAND = "rm -R %(target)s"
    print "removing %(target)s" % {"target": target}
    proc = Popen(RM_COMMAND % {"target": target}, stderr=PIPE, stdout=PIPE, shell=True)
    return proc.wait()

def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H:%m:%S:%f")

def restore_directory(src, target):
    tmpdir = os.path.join(tempfile.gettempdir(), timestamp_string())
    status = move_directory(target, tmpdir)
    if status:
        return status
    status = backup_directory(src, target)
    if status:
        return status
    return remove_directory(src)
    
