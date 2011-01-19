from fabric.api import *
from fab.config import *

'''
Bhoma specific stuff
'''

def syncdb():
    with cd(get_app_dir()):
        sudo('python manage.py syncdb')

def reindex_views():
    with cd(get_app_dir()):
        sudo('python manage.py reindex_views')

def stop_apache():
    sudo("/etc/init.d/apache2 stop")

def start_apache():
    sudo("/etc/init.d/apache2 start")

def stop_formplayer():
    sudo("/etc/init.d/bhoma-formplayer stop")

def start_formplayer():
    sudo("/etc/init.d/bhoma-formplayer start")

def check_server():
    script_loc = PATH_SEP.join((env.root, "bhoma", "scripts", "uptime", "uptime_monitor.py"))
    url = "%s/api/diagnostics/" % env.webapp 
    sudo("python %(script)s %(url)s" % {"script": script_loc, "url": url})

