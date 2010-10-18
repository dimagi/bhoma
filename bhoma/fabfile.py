from datetime import datetime
from fabric.api import *
from fabric.contrib.console import confirm

# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = "/"
TMP_DIR = "/tmp"
SOURCE_DIR = "/var/src/bhoma"
APP_DIR = PATH_SEP.join((SOURCE_DIR, "bhoma"))
BACKUP_DIR = "/var/src/backups"
env.is_local = False

def _cd(dir):
    if env.is_local:
        env.local_dir = dir
    else:
        return cd(dir)

def _sudo(command):
    if env.is_local:
        if env.local_dir:
            Popen("sudo %(cmd)s" % command, stderr=PIPE, stdout=PIPE, shell=True, cwd=env.local_dir)
        else:
            local("sudo %(cmd)s" % command)
    else:
        sudo(command)

def local():
    env.is_local = True
    
def central():
    """Run commands on the central server"""
    env.environment = 'central'
    env.hosts = ['bhoma.cidrz.org']
    env.user = 'bhoma'
    env.root = '/var/src/bhoma'
    env.repo_name = 'cidrz'

def dimagi():
    """Run commands on the central server"""
    env.environment = 'dimagi'
    env.hosts = ['bhoma.dimagi.com']
    env.user = 'bhoma'
    env.root = '/var/src/bhoma'
    env.repo_name = 'origin'
    
def clinic():
    """Run commands on the central server"""
    env.environment = 'clinic'
    env.user = 'bhoma'
    env.root = '/var/src/bhoma'
    env.repo_name = 'cidrz-ext'

def get_app_dir():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    return PATH_SEP.join((env.root, "bhoma"))

def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def fetch():
    """fetch latest code to remote environment """
    _sudo('git fetch %(repo)s master' % {"repo": env.repo_name} )

def fetch_tags():
    """fetch latest tags to remote environment """
    _sudo('git fetch --tags %(repo)s master' % {"repo": env.repo_name} )

def checkout_master():
    """Checks out master"""
    _sudo('git checkout master')

def checkout_tag(tagname):
    """Checks out a tag"""
    _sudo('git checkout %(tagname)s' % {"tagname": tagname } )

def merge():
    """merge latest code to local environment """
    _sudo('git merge %(repo)s' % {"repo": env.repo_name} )

def pull():
    """pull latest code to remote environment """
    _sudo('git pull %(repo)s master' % {"repo": env.repo_name} )

def syncdb():
    with _cd(get_app_dir()):
        _sudo('python manage.py syncdb')

def reindex_views():
    with _cd(get_app_dir()):
        _sudo('python manage.py reindex_views')

def stop_apache():
    _sudo("/etc/init.d/apache2 stop")

def start_apache():
    _sudo("/etc/init.d/apache2 start")

def stop_formplayer():
    _sudo("/etc/init.d/bhoma-formplayer stop")

def start_formplayer():
    _sudo("/etc/init.d/bhoma-formplayer start")

    
def backup_directory(src, target):
    _sudo("cp -Rp %(src)s %(target)s" % {"src": src, "target": target})

def move_directory(src, target):
    _sudo("mv %(src)s %(target)s" % {"src": src, "target": target})

def remove_directory(target):
    _sudo("rm -R %(target)s" % {"target": target})

def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H.%m.%S.%f")

def restore_directory(src, target):
    tmpdir = PATH_SEP.join((TMP_DIR, timestamp_string()))
    move_directory(target, tmpdir)
    backup_directory(src, target)
    remove_directory(src)

def noop():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    run("echo 'hello world'")
    
def update_latest():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    require('repo_name', provided_by=('central', 'dimagi', 'clinic'))
    backup_dir = PATH_SEP.join((BACKUP_DIR, timestamp_string()))
    backup_directory(env.root, backup_dir)
    with _cd(get_app_dir()):
        stop_apache()
        stop_formplayer()
        checkout_master()
        pull()
        syncdb()
        start_formplayer()
        start_apache()
    
def update_tag(tagname):
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    require('repo_name', provided_by=('central', 'dimagi', 'clinic'))
    backup_dir = "%s%s%s" % (BACKUP_DIR, PATH_SEP, timestamp_string())
    backup_directory(env.root, backup_dir)
    with _cd(get_app_dir()):
        stop_apache()
        stop_formplayer()
        try:
            fetch()
            fetch_tags()
            checkout_tag(tagname)
            syncdb()
            remove_directory(backup_dir)
        except SystemExit:
            print "caught abort from fabric!  restoring backup directory."
            with _cd(TMP_DIR):
                restore_directory(backup_dir, SOURCE_DIR)
            raise
        finally:
            start_formplayer()
            start_apache()
