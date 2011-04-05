from fabric.api import *

'''
Fabric config
'''

# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = "/"
TMP_DIR = "/tmp"
SOURCE_DIR = "/var/src/bhoma"
APP_DIR = PATH_SEP.join((SOURCE_DIR, "bhoma"))
BACKUP_DIR = "/var/src/backups"
env.webapp = "http://localhost:8000"
env.root = '/var/src/bhoma'
env.user = 'bhoma'
env.repo_name = 'origin'
env.branch = 'master'
env.notest = False

def git(repo_name="origin", branch="master"):
    """Set a custom git repository or branch.  Must be run like one of the following:
    git:repo_name=daemon
    git:branch=paper_form_update
    git:repo_name=daemon,branch=paper_form_update
    """
    env.repo_name = repo_name
    env.branch = branch
    
def central():
    """Run commands on the central server"""
    env.environment = 'central'
    env.hosts = ['bhoma.cidrz.org']
    env.webapp = "http://bhoma.cidrz.org"

def dimagi():
    """Run commands on the dimagi server"""
    env.environment = 'dimagi'
    env.hosts = ['bhoma.dimagi.com']
    env.webapp = "http://bhoma.dimagi.com"
    
def clinic():
    """Run commands on a clinic server"""
    env.hosts = ['localhost']
    env.environment = 'clinic'
    env.webapp = "http://10.10.10.10"

def notest():
    """Don't test apache after updating"""
    env.notest = True
    
def get_app_dir():
    return PATH_SEP.join((env.root, "bhoma"))

