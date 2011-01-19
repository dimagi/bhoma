from datetime import datetime
from subprocess import Popen, PIPE
from fabric.api import *
from fabric.contrib.console import confirm
from fab.config import *
from fab.os import *
from fab.git import *
from fab.bhoma import *
from fab.central import *

def test():
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def _protected_update(inner_update):
    """
    Shared functionality around a protected update, which backs up
    and restores the directory if anyhing fails
    """
    require('repo_name', provided_by=('daemon', 'dimagi', 'clinic', 'daemon'))
    require('repo_name', provided_by=('central', 'dimagi', 'clinic', 'daemon'))
    create_directory(BACKUP_DIR)
    backup_dir = PATH_SEP.join((BACKUP_DIR, timestamp_string()))
    backup_directory(env.root, backup_dir)
    with cd(get_app_dir()):
        stop_apache()
        stop_formplayer()
        if env.environment == "central":
            # stop a few more things only available/running on the central server
            stop_central_server_scripts()
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
        finally:
            if env.environment == "central":
                start_central_server_scripts()
                
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

def migrate_rev2():
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    with cd(get_app_dir()):
        # replicate database to backup
        run("python manage.py backup_db bhoma_rev_1 --noinput")
        # delete database
        run("python manage.py delete_db --noinput")
        # sync database
        run("python manage.py syncdb")
        # migrate user accounts
        # TODO