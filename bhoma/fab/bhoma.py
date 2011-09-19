from fabric.api import *
from fab.config import *

'''
Bhoma specific stuff
'''

def syncdb():
    sudo('python manage.py syncdb')

def reset_forms():
    sudo('python manage.py reset formplayer --noinput')

def collectstatic():
    sudo('python manage.py collectstatic --noinput')

def reindex_views():
    sudo('python manage.py reindex_views')

def stop_apache():
    sudo("/etc/init.d/apache2 stop")

def start_apache():
    sudo("/etc/init.d/apache2 start")

def stop_formplayer():
    sudo("/etc/init.d/bhoma-formplayer stop")

def start_formplayer():
    sudo("/etc/init.d/bhoma-formplayer start")

def stop_couchdb():
    sudo('service couchdb stop')

def start_couchdb():
    sudo('service couchdb start')

def check_server():
    script_loc = PATH_SEP.join((env.root, "bhoma", "scripts", "uptime", "uptime_monitor.py"))
    url = "%s/api/diagnostics/" % env.webapp 
    sudo("python %(script)s %(url)s" % {"script": script_loc, "url": url})
