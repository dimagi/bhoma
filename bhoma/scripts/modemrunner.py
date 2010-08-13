from subprocess import Popen, PIPE
import time

# this is an excellent reference for calling shell commands from python:
# http://stackoverflow.com/questions/89228/how-to-call-external-command-in-python

# TODO: google python script test if you are connected to the internet
def wvdial_success(proc):
    # give it some time to do its thing
    time.sleep(5)
    # hacky hacky, just check the output to see if we're happy
    out = proc.stdout.read()
    return "IP address" in stdout
    

def test_public_connection():
    # hacky hacky
    ping_proc = Popen("ping -c 3 google.com", stdout=PIPE, shell=True)
    ret = ping_proc.wait()
    out = ping_proc.stdout.read()
    # TODO: ping in python?
    return not "0 received" in out
    
wvdial_proc = Popen("echo Hello World", stdout=PIPE, shell=True)
if wvdial_success(wvdial_proc):
    print "wvdial thinks it has a connection"
    if test_public_connection():
        print "public connection successful!"
    else:
        print "failed to connect!"