from datetime import datetime
import tempfile
from fabric.api import *
from fabric.contrib.console import confirm

# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = "/"
SOURCE_DIR = "/var/src/bhoma"
APP_DIR = "%s%sbhoma" % (SOURCE_DIR, PATH_SEP)
BACKUP_DIR = "/var/src/backups"

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
    
def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def fetch():
    """fetch latest code to remote environment """
    sudo('git fetch %(repo)s master' % {"repo": env.repo_name} )

def merge():
    """merge latest code to local environment """
    sudo('git merge %(repo)s' % {"repo": env.repo_name} )

def pull():
    """pull latest code to remote environment """
    sudo('git pull %(repo)s master' % {"repo": env.repo_name} )

def syncdb():
    sudo('python manage.py syncdb')

def stop_apache():
    sudo("/etc/init.d/apache2 stop")

def start_apache():
    sudo("/etc/init.d/apache2 start")

def stop_formplayer():
    sudo("/etc/init.d/bhoma-formplayer stop")

def start_formplayer():
    sudo("/etc/init.d/bhoma-formplayer start")

    
def backup_directory(src, target):
    sudo("cp -Rp %(src)s %(target)s" % {"src": src, "target": target})

def move_directory(src, target):
    sudo("mv %(src)s %(target)s" % {"src": src, "target": target})

def remove_directory(target):
    sudo("rm -R %(target)s" % {"target": target})

def timestamp_string():
    return datetime.now().strftime("%Y-%m-%d-%H:%m:%S:%f")

def restore_directory(src, target):
    tmpdir = os.path.join(tempfile.gettempdir(), timestamp_string())
    move_directory(target, tmpdir)
    backup_directory(src, target)
    remove_directory(src)

def noop():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    run("echo 'hello world'")
    
def update():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    require('repo_name', provided_by=('central', 'dimagi', 'clinic'))
    backup_dir = "%s%s%s" % (BACKUP_DIR, PATH_SEP, timestamp_string())
    backup_directory(SOURCE_DIR, backup_dir)
    with cd(APP_DIR):
        stop_apache()
        stop_formplayer()
        pull()
        syncdb()
        start_formplayer()
        start_apache()
    
def prepare_deploy():
    test()
    pack()

def deploy():
    put('/tmp/bhoma.tgz', '/tmp/')
    with cd('/var/src/bhoma/bhoma/'):
        run('tar xzf /tmp/bhoma.tgz')
        

