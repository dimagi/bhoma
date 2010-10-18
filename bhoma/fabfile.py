from datetime import datetime
import tempfile
from fabric.api import *
from fabric.contrib.console import confirm

# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = "/"
SOURCE_DIR = "/var/src/bhoma"
APP_DIR = "%s%sbhoma" % (SOURCE_DIR, PATH_SEP)
BACKUP_DIR = "/var/src/backups"

def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def fetch():
    """fetch latest code to remote environment """
    sudo('git fetch origin master')

def merge():
    """merge latest code to local environment """
    sudo('git merge origin')


def pull():
    """pull latest code to remote environment """
    sudo('git pull origin master')

def stop_apache():
    sudo("/etc/init.d/apache2 stop")

def start_apache():
    sudo("/etc/init.d/apache2 start")

    
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

def update():
    backup_dir = "%s%s%s" % (BACKUP_DIR, PATH_SEP, timestamp_string())
    backup_directory(SOURCE_DIR, backup_dir)
    with cd(SOURCE_DIR):
        stop_apache()
        pull()
        start_apache()
    
def prepare_deploy():
    test()
    pack()

def deploy():
    put('/tmp/bhoma.tgz', '/tmp/')
    with cd('/var/src/bhoma/bhoma/'):
        run('tar xzf /tmp/bhoma.tgz')
        

