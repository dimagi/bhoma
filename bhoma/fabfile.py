from fabric.api import *
from fabric.contrib.console import confirm


def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def pack():
    local('tar czf /tmp/bhoma.tgz .', capture=False)

def prepare_deploy():
    test()
    pack()

def deploy():
    put('/tmp/bhoma.tgz', '/tmp/')
    with cd('/var/src/bhoma/bhoma/'):
        run('tar xzf /tmp/bhoma.tgz')
        
