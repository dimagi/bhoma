from fabric.api import *
from fab.config import *

'''
Git Commands
'''

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


