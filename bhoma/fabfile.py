from datetime import datetime
from subprocess import Popen, PIPE
from fabric.api import *
from fabric.contrib.console import confirm

# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = "/"
TMP_DIR = "/tmp"
SOURCE_DIR = "/var/src/bhoma"
APP_DIR = PATH_SEP.join((SOURCE_DIR, "bhoma"))
BACKUP_DIR = "/var/src/backups"
env.webapp = "http://localhost:8000"


def _common_config():
    env.user = 'bhoma'
    env.root = '/var/src/bhoma'
    

def central():
    """Run commands on the central server"""
    _common_config()
    env.environment = 'central'
    env.hosts = ['bhoma.cidrz.org']
    env.repo_name = 'origin'
    env.webapp = "http://bhoma.cidrz.org"

def dimagi():
    """Run commands on the central server"""
    _common_config()
    env.environment = 'dimagi'
    env.hosts = ['bhoma.dimagi.com']
    env.repo_name = 'origin'
    env.webapp = "http://bhoma.dimagi.com"
    
def clinic():
    """Run commands on the central server"""
    _common_config()
    env.environment = 'clinic'
    env.repo_name = 'cidrz-ext'
    env.webapp = "http://10.10.10.10"

def get_app_dir():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    return PATH_SEP.join((env.root, "bhoma"))

def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def fetch():
    """fetch latest code to remote environment """
    sudo('git fetch %(repo)s master' % {"repo": env.repo_name} )

def fetch_tags():
    """fetch latest tags to remote environment """
    sudo('git fetch --tags %(repo)s master' % {"repo": env.repo_name} )

def checkout_master():
    """Checks out master"""
    sudo('git checkout master')

def checkout_tag(tagname):
    """Checks out a tag"""
    sudo('git checkout %(tagname)s' % {"tagname": tagname } )

def merge():
    """merge latest code to local environment """
    sudo('git merge %(repo)s' % {"repo": env.repo_name} )

def pull():
    """pull latest code to remote environment """
    sudo('git pull %(repo)s master' % {"repo": env.repo_name} )

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

def create_directory(dir):
    sudo("mkdir -p %(dir)s" % {"dir" : dir})

def backup_directory(src, target):
    sudo("cp -Rp %(src)s %(target)s" % {"src": src, "target": target})

def move_directory(src, target):
    sudo("mv %(src)s %(target)s" % {"src": src, "target": target})

def remove_directory(target):
    sudo("rm -R %(target)s" % {"target": target})

def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H.%m.%S.%f")

def restore_directory(src, target):
    tmpdir = PATH_SEP.join((TMP_DIR, timestamp_string()))
    move_directory(target, tmpdir)
    backup_directory(src, target)
    remove_directory(src)

def check_server():
    script_loc = PATH_SEP.join((env.root, "bhoma", "scripts", "uptime", "uptime_monitor.py"))
    url = "%s/api/diagnostics/" % env.webapp 
    sudo("python %(script)s %(url)s" % {"script": script_loc, "url": url})

def noop():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    run("echo 'hello world'")
    

def _protected_update(inner_update):
    """
    Shared functionality around a protected update, which backs up
    and restores the directory if anyhing fails
    """
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    require('repo_name', provided_by=('central', 'dimagi', 'clinic'))
    create_directory(BACKUP_DIR)
    backup_dir = PATH_SEP.join((BACKUP_DIR, timestamp_string()))
    backup_directory(env.root, backup_dir)
    with cd(get_app_dir()):
        stop_apache()
        stop_formplayer()
        try:
            inner_update()
            start_formplayer()
            start_apache()
            check_server()
        except SystemExit:
            print "caught abort from fabric!  restoring backup directory."
            with cd(TMP_DIR):
                restore_directory(backup_dir, SOURCE_DIR)
            start_formplayer()
            start_apache()
            # if this fails we're kinda screwed, but at least 
            # we might know from email notifications
            check_server()
            raise
             
            
def update_latest():
    def inner_update():
        checkout_master()
        pull()
        syncdb()
        
    _protected_update(inner_update)
    
def update_tag(tagname):
    def inner_update():
        fetch()
        fetch_tags()
        checkout_tag(tagname)
        syncdb()
    
    _protected_update(inner_update)