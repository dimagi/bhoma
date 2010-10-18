from fabric.api import *
from fabric.contrib.console import confirm


def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def fetch():
    """fetch latest code to remote environment """
    run('git fetch origin master')

def merge():
    """merge latest code to local environment """
    run('git merge origin')


def pull():
    """pull latest code to remote environment """
    run('git pull origin master')

def stop_apache():
    run("/etc/init.d/apache2 stop")

def start_apache():
    run("/etc/init.d/apache2 start")

def update():
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
        

