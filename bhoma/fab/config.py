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
    """Run commands on the dimagi server"""
    _common_config()
    env.environment = 'dimagi'
    env.hosts = ['bhoma.dimagi.com']
    env.repo_name = 'origin'
    env.webapp = "http://bhoma.dimagi.com"
    
def clinic():
    """Run commands on a clinic server"""
    _common_config()
    env.environment = 'clinic'
    env.repo_name = 'origin'
    env.webapp = "http://10.10.10.10"

def get_app_dir():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    return PATH_SEP.join((env.root, "bhoma"))

