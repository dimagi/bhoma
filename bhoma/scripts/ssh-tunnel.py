import os
import os.path

# script to setup a reverse ssh tunnel (still in development)
# to use this: 
# copy localsshsettings.py.example to localsshsettings.py
# fill in the appropriate user and port information
# run ssh-tunnel.py

SERVER = '41.194.0.74'

from localsshsettings import *

# the above should import USER and PORT or fail.

ssh_cmd = 'ssh -i %s@%s -N -R %d:localhost:22 -C -o "BatchMode yes" -o "ExitOnForwardFailure yes" -o "ServerAliveInterval 60"' % \
        (USER, SERVER, PORT)

os.popen(ssh_cmd)