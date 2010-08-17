from subprocess import Popen, PIPE
import time

# this is an excellent reference for calling shell commands from python:
# http://stackoverflow.com/questions/89228/how-to-call-external-command-in-python

# TODO: use python script to test if you are connected to the internet.
# testing with ping is pretty janky  
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
            print "ERROR: wvdial exited with code %s" % code
            return False
        # give it some time to do its thing
        print "going to sleep for %s seconds, total wait time is %s seconds" % \
            (INTERVAL_TIME, wait_time)
        time.sleep(INTERVAL_TIME)
        wait_time += INTERVAL_TIME

    return True
    # TODO: hacky hacky, just check the output to see if we're happy
    # return "IP address" in out
    

def test_public_connection():
    # hacky hacky
    print "pinging google to test public connection."
    ping_proc = Popen("ping -c 5 google.com", stdout=PIPE, stderr=PIPE, shell=True)
    ret = ping_proc.wait()
    if ret == 0:
        out = ping_proc.stdout.read()
        # TODO: ping/test in native python?
        return not "0 received" in out
    print "ping failed! %s" % ping_proc.stderr.read()
    return False

def full_modem_config():
    if test_public_connection():
        print "already connected!"
        return True
    else: 
        print "not connected starting wvdial"
        wvdial_configs = ["defaults", "alt1", "alt2", "alt3"]
        for conf in wvdial_configs:
            command = "wvdial %s" % conf
            print "running %s" % command
            wvdial_proc = Popen(command, stdout=PIPE, shell=True)
            if wvdial_success(wvdial_proc):
                print "wvdial thinks it has a connection"
                if test_public_connection():
                    print "public connection successful!"
                    return True
                else:
                    print "failed to connect!"

        # down here we failed.
        return False

if __name__ == "__main__":
    full_modem_config()
