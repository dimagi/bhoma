import os
import os.path
from subprocess import Popen
import re
import time
import json

# create an ssh tunnel between clinic and central server

# requirements:

# * per-clinic ssh user and reverse-ssh port settings defined in localsshsettings.py
#   (see localsshsettings.py.example)
# * verify that the user this script will run under has write access to 'TMP_DIR'

# instructions:
# * run script with no arguments; script will not terminate until tunnel is closed
#   (we hope; theoretically tunnel might close but script stays running -- this is
#   what the failsafe protects against)
# * for deployment, run as a cronjob every minute

# it is safe to attempt reconnection while an open tunnel already exists; the
# reconnection will fail harmlessly because the forwarded ports are in use.
# however each connection attempt uses 5-9KB of bandwidth and that can add up
# over time. thus, to save bandwidth, we can attempt reconnection only when we
# see the previous tunneling process is no longer running. but if that tunnel
# somehow gets into a stale state where the process is still running but the
# connection has otherwise been severed, the tunnel won't ever come back. so,
# we'll still attempt reconnection even if the previous process is still
# running every 'FAILSAFE_INTERVAL' seconds (set to 0 to attempt connection
# every time)
FAILSAFE_INTERVAL = 1200

TMP_DIR = '/var/lib/bhoma'
PIDFILE_DIR = os.path.join(TMP_DIR, 'sshtunnel.pids')
LAST_CONNECT_ATTEMPT_FILE = os.path.join(TMP_DIR, 'sshtunnel.last_connect_attempt')

def mk_port_forward(listen_at, local_port, remote_port):
    if listen_at == 'forward':
        return '-L %d:localhost:%d' % (local_port, remote_port)
    elif listen_at == 'reverse':
        return '-R %d:localhost:%d' % (remote_port, local_port)

def mk_port_forwards(port_forwards):
    return ' '.join(mk_port_forward(*f) for f in port_forwards)

def mk_tunnel_cmd(user, server, forwards, compression=True, keyfile=None):
    options = [
        'BatchMode yes',
        'ExitOnForwardFailure yes',
        'ServerAliveInterval 60',
    ]

    return 'ssh %s@%s -N %s %s %s %s' % (user, server, '-C' if compression else '', '-i %s' % keyfile if keyfile else '',
                                      mk_port_forwards(forwards), ' '.join('-o "%s"' % opt for opt in options))

def pidfile(pid):
    return os.path.join(PIDFILE_DIR, str(pid))

def set_pid(pid):
    try:
        with open(pidfile(pid), 'w') as f:
            pass
    except IOError:
        pass

def unset_pid(pid):
    try:
        os.remove(pidfile(pid))
    except OSError:
        pass

# given a pid, guess if it corresponds to a running tunnel process by
# examining the pidfiles and /proc
def validate_pid(pid):
    path = pidfile(pid)
    if os.path.exists(path):
        try:
            with open('/proc/%d/cmdline' % pid) as f:
                cmdargs = f.read().split('\0')
            running = any(re.match('^ssh(?![^\s])', arg) for arg in cmdargs)
        except IOError:
            running = False

        if not running:
            unset_pid(pid)
        return running
    else:
        return False

def get_pids():
    pids = []
    try:
        dirlist = os.listdir(PIDFILE_DIR)
    except OSError:
        dirlist = []
    for pid in dirlist:
        try:
            pids.append(int(pid))
        except ValueError:
            pass
    return pids

# guess if a tunnel process is running based on pidfiles
def is_tunnel_up():
    return any(validate_pid(pid) for pid in get_pids())

def set_connect_time(stamp=None):
    try:
        with open(LAST_CONNECT_ATTEMPT_FILE, 'w') as f:
            f.write('%d\n' % (stamp if stamp else time.time()))
    except IOError:
        pass

def get_connect_time():
    try:
        with open(LAST_CONNECT_ATTEMPT_FILE) as f:
            return int(f.read().strip())
    except (IOError, ValueError):
        return None

# determine if we're in 'failsafe mode' based on time elapsed since the
# last-known connection attempt
def is_failsafe():
    now = time.time()
    last_connect = get_connect_time()

    return (last_connect is None or now - last_connect > FAILSAFE_INTERVAL or now < last_connect)

def setup():
    if not os.path.exists(PIDFILE_DIR):
        try:
            os.mkdir(PIDFILE_DIR)
        except:
            pass

def get_settings(app_dir):
    config = json.load(os.popen('python %s revsshconfig' % os.path.join(app_dir, 'manage.py')))
    return (config[k] for k in ('server', 'user', 'port'))

if __name__ == "__main__":

    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SERVER, USER, PORT = get_settings(APP_DIR)
    PORT_FORWARDS = [
        ('reverse',   22, PORT), #reverse ssh
        ('forward', 6984, 5984), #couch replication through tunnel
    ]

    setup()

    tunnel_up = is_tunnel_up()
    failsafe = is_failsafe()

    if not tunnel_up or failsafe:
        p = Popen(mk_tunnel_cmd(USER, SERVER, PORT_FORWARDS), shell=True)
        set_connect_time()
        set_pid(p.pid)
        p.wait()
        unset_pid(p.pid)
