from fabric.api import *
from fabric.contrib.console import confirm
from fab.config import *
import fab.os as fab_os
import fab.git as fab_git
import fab.bhoma as fab_bhoma
import fab.central as fab_central

def test():
    """Run local bhoma unit tests"""
    local('python manage.py test patient case reports xforms couchlog', capture=False)
    
def _protected_update(inner_update):
    """
    Shared functionality around a protected update, which backs up
    and restores the directory if anyhing fails
    """
    require('environment', provided_by=('central', 'dimagi', 'clinic', 'daemon'))
    fab_os.create_directory(BACKUP_DIR)
    backup_dir = PATH_SEP.join((BACKUP_DIR, fab_os.timestamp_string()))
    fab_os.backup_directory(env.root, backup_dir)
    with cd(get_app_dir()):
        fab_bhoma.stop_apache()
        fab_bhoma.stop_formplayer()
        if env.environment == "central":
            # stop a few more things only available/running on the central server
            fab_central.stop_central_server_scripts()
        try:
            inner_update()
            fab_bhoma.start_formplayer()
            fab_bhoma.start_apache()
            fab_bhoma.check_server()
        except SystemExit:
            print "caught abort from fabric!  restoring backup directory."
            with cd(TMP_DIR):
                fab_os.restore_directory(backup_dir, SOURCE_DIR)
            fab_bhoma.start_formplayer()
            fab_bhoma.start_apache()
            # if this fails we're kinda screwed, but at least 
            # we might know from email notifications
            fab_bhoma.check_server()
            raise
        finally:
            if env.environment == "central":
                fab_central.start_central_server_scripts()
                
def update_latest():
    """Update to the latest version of the code"""
    def inner_update():
        fab_git.checkout_branch()
        fab_git.pull()
        fab_bhoma.syncdb()
        
    _protected_update(inner_update)
    
def update_tag(tagname):
    """Update to a specific tag (run fab update_tag:tagname)"""
    def inner_update():
        fab_git.fetch()
        fab_git.fetch_tags()
        fab_git.checkout_tag(tagname)
        fab_bhoma.syncdb()
    
    _protected_update(inner_update)

def migrate_rev2():
    """Migrate the application from rev1 to rev2"""
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    with cd(get_app_dir()):
        # replicate database to backup
        run("python manage.py backup_db bhoma_rev_1 --noinput")
        # delete database
        run("python manage.py delete_db --noinput")
        # sync database
        run("python manage.py syncdb")
        # migrate user accounts
        run("python manage.py migrate_rev2_data")
        