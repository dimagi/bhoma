from datetime import datetime, timedelta
import os

""" 
This little script is meant to be run when x starts.  If it hasn't been
started recently (set by a flag in a file) it restarts x.  Otherwise it
just writes the new date flag to the file.  This is used by the touchscreens
which sometimes boot in a way that doesn't load the drivers, so we just 
always restart X on a fresh boot.
"""
LOGFILE = os.path.join(os.path.dirname(__file__), "xbootlog.txt")
DATE_FORMAT = '%b %d %Y %I:%M%p'
WINDOW_IN_MINUTES = 3 # this is how in the past we don't restart x for
X_RESTART_COMMAND = "/etc/init.d/gdm restart"

def restart_x():
    print "RESTARTING XWINDOWS NOW!"
    os.popen(X_RESTART_COMMAND)

def date_from_logfile():
    if os.path.exists(LOGFILE):
        f = None
        try:
            f = open(LOGFILE, 'r')
            datestr = f.read()
            return datetime.strptime(datestr, DATE_FORMAT)
        except Exception, e:
            print "problem getting time! %s" % e
        finally:
            if f: f.close()
    return None
    
def write_new_logfile():
    f = open(LOGFILE, "w")
    f.write("%s" % datetime.now().strftime(DATE_FORMAT))
    f.close()


now = datetime.now()
last_run_date = date_from_logfile()
should_restart_x = last_run_date and now - last_run_date > timedelta(minutes=WINDOW_IN_MINUTES)
write_new_logfile()
if    should_restart_x: restart_x()
else:                   print "no need to restart!"
    
