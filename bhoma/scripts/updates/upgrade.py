import sys, os
from datetime import datetime
from subprocess import Popen, PIPE, call
from bhoma.scripts.updates.operations import SUCCESS, git_fetch,\
    backup_directory, timestamp_string, simulate_failure, restore_directory


""" 
A script to remotely update BHOMA servers.  This script should perform the 
following:
    remotely fetch new code
    verify code download (e.g. hash of files)
    take down server, display "you are upgrading dialog"
    backup database(s)
    backup code directory
    apply new code updates
    verify code update (e.g. hash of files)
    apply database update (if necessary)
    run tests
    if success
    startup server
    verify server update
    else
    restore old database
    restore old code
    report error
    startup server
    verify server restore
    
This very much only works on linux servers.
"""
SOURCE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def noop():
    pass

def verify_status(status, msg, callback_fail=sys.exit, callback_success=noop):
    if status != SUCCESS:
        print "%s FAILED" % msg
        callback_fail()
    else:
        print "%s SUCCESS"
        callback_success()

def bhoma_update_all():
    # check if running as root
    def running_as_root():
        return os.geteuid() == 0 
    
    if not running_as_root():
        print "Sorry, this command must be run as root.  Run the same command with sudo."
        sys.exit()
    print "updating bhoma!"
    
    
    verify_status(git_fetch(), "Fetching the code.")
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backups", timestamp_string())
    verify_status(backup_directory(SOURCE_DIR, target_dir), "Backing up the current source directory.")
    
    def restore_backup():
        print "restoring backup"
        restore_directory(target_dir, SOURCE_DIR)
    
    verify_status(simulate_failure(), callback_fail=restore_backup)
    print "exiting"
        
    
    
if __name__ == "__main__":
    bhoma_update_all()
