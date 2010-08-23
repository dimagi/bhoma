from subprocess import Popen, PIPE, call
import time

# this is an excellent reference for calling shell commands from python:
# http://stackoverflow.com/questions/89228/how-to-call-external-command-in-python

# TODO: use python script to test if you are connected to the internet.
# testing with ping is pretty janky

PROC_IDS_COMMAND = "ps aux | grep -i '%(proc)s' | grep -v grep | awk '{print $2}'" 

def log(msg):
    print msg
    
def test_public_connection():
    # hacky hacky
    log("pinging google to test public connection.")
    ping_proc = Popen("ping -c 5 google.com", stdout=PIPE, stderr=PIPE, shell=True)
    ret = ping_proc.wait()
    if ret == 0:
        out = ping_proc.stdout.read()
        # TODO: ping/test in native python?
        return not "0 received" in out
    log("ping failed! %s" % ping_proc.stderr.read())
    return False

def wvdial_success(proc):
    # hack
    # We assume that if it hasn't returned after this amount of time then
    # it is happy
    TIMEOUT = 20
    wait_time = 0
    INTERVAL_TIME = 5
    while wait_time < TIMEOUT:
        # if it returned, something bad happened
        code = proc.poll()
        if code:
            log("ERROR: wvdial exited with code %s" % code)
            return False
        # give it some time to do its thing
        log("going to sleep for %s seconds, total wait time is %s seconds" % \
            (INTERVAL_TIME, wait_time))
        time.sleep(INTERVAL_TIME)
        wait_time += INTERVAL_TIME

    return True
    # TODO: hacky hacky, just check the output to see if we're happy
    # return "IP address" in out

def get_process_ids(command):
    proc = Popen(PROC_IDS_COMMAND % {"proc": command}, stdout=PIPE, stderr=PIPE, shell=True)
    proc.wait()
    out = proc.stdout.read()
    log("active %s processes: %s" % (command, out))
    return [proc for proc in out.split("\n") if proc.strip()]

def kill_processes(command, sleep_interval = 2):
    ids =  get_process_ids(command)
    for proc_id in ids:
        call("kill -9 %s" % proc_id, shell=True)
    time.sleep(sleep_interval)
    if get_process_ids(command):
        log("killing %s processes failed! Processes still alive: %s" % (command, get_process_ids(command)))
        return False
    elif ids:
        log("Successfully killed %s %s processes" % (len(ids), command))
    else:
        log("no %s processes found" % command)
    return True
    
def full_modem_config():
    if test_public_connection():
        log("already connected!")
        return True
    else: 
        log("not connected, restarting wvdial")
        # first kill all known instances of wvdial and pppd
        should_proceed = kill_processes("wvdial") and kill_processes("pppd")
        if not should_proceed:
            log("unable to kill active wvdial or pppd processes.  exiting")
            return 1
        # wvdial_configs = ["defaults", "alt1", "alt2", "alt3"]
        wvdial_configs = ["defaults"]
        for conf in wvdial_configs:
            command = "wvdial %s" % conf
            log("running %s" % command)
            wvdial_proc = Popen(command, stdout=PIPE, shell=True)
            if wvdial_success(wvdial_proc):
                log("wvdial thinks it has a connection")
                if test_public_connection():
                    log("public connection successful!")
                    return True
                else:
                    log("failed to connect!")

        # down here we failed.
        return False

if __name__ == "__main__":
    full_modem_config()
