from fabric.api import *
from fab.config import *

'''
Git Commands
'''

def fetch():
    """fetch latest code to remote environment """
    sudo('git fetch %(repo)s %(branch)s' % {"repo": env.repo_name, "branch": env.branch} )

def fetch_tags():
    """fetch latest tags to remote environment """
    sudo('git fetch --tags %(repo)s %(branch)s' % {"repo": env.repo_name, "branch": env.branch} )

def checkout_branch():
    """Checks out master"""
    sudo('git checkout %(branch)s' % {"branch": env.branch})

def checkout_tag(tagname):
    """Checks out a tag"""
    sudo('git checkout %(tagname)s' % {"tagname": tagname } )

def merge():
    """merge latest code to local environment """
    sudo('git merge %(repo)s' % {"repo": env.repo_name} )

def pull():
    """pull latest code to remote environment """
    sudo('git pull %(repo)s %(branch)s' % {"repo": env.repo_name, "branch": env.branch} )

def update_submodules():
    """Initializes and updates submodules"""
    sudo('git submodule init')
    sudo('git submodule update')

def clean():
    sudo('find -iname \'*.pyc\' -print0 | xargs -0 rm')
