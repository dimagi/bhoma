from fabric.api import *
from fabric.contrib.console import confirm
from fab.config import *
import fab.os as fab_os
import fab.git as fab_git
import fab.bhoma as fab_bhoma
import fab.central as fab_central
from datetime import datetime
import os.path
import os
import dateutil.tz
import re
from fabric import colors
import sys
from contextlib import contextmanager
import tempfile

def test():
    """Run local bhoma unit tests"""
    local('python manage.py test patient case reports xforms couchlog bhomalog phone', capture=False)
    
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
            if env.test: 
                fab_bhoma.check_server()
        except SystemExit:
            print "caught abort from fabric!  restoring backup directory."
            with cd(TMP_DIR):
                fab_os.restore_directory(backup_dir, SOURCE_DIR)
            fab_bhoma.start_formplayer()
            fab_bhoma.start_apache()
            # if this fails we're kinda screwed, but at least 
            # we might know from email notifications
            if env.test:
                fab_bhoma.check_server()
            raise
        finally:
            if env.environment == "central":
                fab_central.load_zones()
                fab_central.start_central_server_scripts()
                
def update_latest():
    """Update to the latest version of the code"""
    def inner_update():
        fab_git.checkout_branch()
        fab_git.pull()
        with cd(env.root):
            # this must be run in the root git directory
            fab_git.update_submodules()
            fab_git.clean()
        fab_bhoma.reset_forms()
        fab_bhoma.collectstatic()
        fab_bhoma.syncdb()
        
    _protected_update(inner_update)
    
def update_tag(tagname):
    """Update to a specific tag (run fab update_tag:tagname)"""
    def inner_update():
        fab_git.fetch()
        fab_git.fetch_tags()
        fab_git.checkout_tag(tagname)
        with cd(env.root):
            # this must be run in the root git directory
            fab_git.update_submodules()
            fab_git.clean()
        fab_bhoma.reset_forms()
        fab_bhoma.collectstatic()
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
        fab_bhoma.syncdb()
        # migrate user accounts
        run("python manage.py migrate_rev2_data bhoma_rev_1")
        update_crontabs()

def migrate_v022_v023():
    """Migrate the app from v0.2.2 to v0.2.3"""
    require('root', provided_by=('central', 'dimagi', 'clinic'))
    with cd(get_app_dir()):
        # delete export design doc in clinics
        run("python manage.py remove_export_design_doc")

def update_crontabs():
    """
    Set appropriate crontabs for root and bhoma users
    """
    root_tab = PATH_SEP.join((get_app_dir(), "sysconfig", "clinic_root.crontab"))
    bhoma_tab = PATH_SEP.join((get_app_dir(), "sysconfig", "clinic_bhoma.crontab"))
    sudo('crontab -u root %s' % root_tab)
    sudo('crontab -u bhoma %s' % bhoma_tab)

#hard-coded for now (likely forever)
COUCH_DATA_DIR = '/usr/local/var/lib/couchdb'
COUCH_USER = 'couchdb'
COUCH_DB_DEFAULT = 'bhoma'

def preupgrade(backup_volume):
    hostname = run('hostname').strip()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_token = '%s_%s' % (hostname, timestamp)
    backup_dir = os.path.join(backup_volume, 'ugbk_%s' % backup_token)

    try:
        os.mkdir(backup_dir)
    except:
        _print("""\
ERROR making backup dir: backup drive is not mounted, mis-typed, read-only, or
backup dir already exists!""", True)
        raise

    fab_bhoma.stop_apache()
    _stop_couchdb()

    _print('backing up configuration settings')
    paranoid_backup(os.path.join(APP_DIR, 'localsettings.py'), backup_dir)

    _print('backing up couch database')
    couch_db = get_django_setting('BHOMA_COUCH_DATABASE_NAME', COUCH_DB_DEFAULT)
    paranoid_backup(os.path.join(COUCH_DATA_DIR, '%s.couch' % couch_db), os.path.join(backup_dir, 'db.couch'), sudo)

    _print('backing up postgres database')
    #with cd(APP_DIR):
    #    run('python manage.py dumpdata > "%s"' % os.path.join(backup_dir, 'postgres_db.json'))
    with postgres_op() as pgrun:
        pgrun('pg_dump {{db}} > /tmp/pgdump')
    paranoid_backup('/tmp/pgdump', os.path.join(backup_dir, 'postgres_db.pgsql'))

    _print("""
  clinic data has been backed up to %s
  make sure this directory is on an external drive that will not be deleted
  when this server is re-ghosted!!

  to restore clinic data on the upgraded server, run:
    fab clinic postupgrade:%s""" % (backup_dir, backup_dir))

# needed for bootstrapping, until fab/bhoma.py is upgraded
def _stop_couchdb():
    try:
        fab_bhoma.stop_couchdb()
    except AttributeError:
        sudo('service couchdb stop', pty=False)

# needed for bootstrapping, until fab/bhoma.py is upgraded
def _start_couchdb():
    try:
        fab_bhoma.start_couchdb()
    except AttributeError:
        sudo('service couchdb start', pty=False)

def get_django_setting(setting_name, fallback=None):
    # the necessary mgmt cmd might not exist yet, hence the fallback
    with settings(warn_only=True):
        with cd(APP_DIR):
            setting = run('python manage.py exec "from django.conf import settings; print settings.%s" 2> /dev/null' % setting_name)
    return setting.strip() if not setting.failed else fallback

def clock_str():
    return datetime.now(dateutil.tz.tzlocal()).strftime('%Y-%m-%d %H:%M:%S %z')

def postupgrade(backup_dir):
    if not os.path.exists(backup_dir) or not os.path.isdir(backup_dir):
        _print('cannot find backup dir [%s]' % backup_dir, True)
        sys.exit()

    if backup_dir.endswith('/'):
        backup_dir = os.path.dirname(backup_dir)

    fab_bhoma.stop_apache()
    _stop_couchdb()

    _print('restoring configuration settings')
    paranoid_restore(os.path.join(backup_dir, 'localsettings.py'), APP_DIR)
    # it is possible localsettings needs to be updated with new required settings before we can proceed with the restore

    _print('restoring postgres database')
    #with cd(APP_DIR):
    #    _start_couchdb() #couchdb must be running for db ops else couchdbkit complains
    #    run('python manage.py flush --noinput')
    #    run('python manage.py loaddata "%s"' % os.path.join(backup_dir, 'postgres_db.json'))
    #    run('python manage.py syncdb')
    #    _stop_couchdb()
    #    # how do we handle database migrations here?
    paranoid_restore(os.path.join(backup_dir, 'postgres_db.pgsql'), '/tmp/pgdump')
    with postgres_op() as pgrun:
        pgrun('dropdb {{db}}')
        pgrun('createdb {{db}}')
        pgrun('psql {{db}} -f /tmp/pgdump')
    #run db migrations here?
    _start_couchdb()
    with cd(APP_DIR):
        run('python manage.py syncdb')
    _stop_couchdb()

    _print('setting hostname')
    hostname = get_django_setting('SYSTEM_HOSTNAME')
    _print('no hostname in localsettings.py; attempting to extract from backup dir')
    try:
        hostname = re.match('ugbk_(.+)_[0-9]{14}$', os.path.split(backup_dir)[1]).group(1)
    except AttributeError:
        hostname = None
    if not hostname:
        _print('unable to determine system hostname!', True)
        sys.exit()
    _print('using [%s] as hostname' % hostname)
    sudo('echo %s > /etc/hostname' % hostname)

    # don't think we really need to update /etc/hosts; punting...

    _print('restoring couch database')
    couch_db = get_django_setting('BHOMA_COUCH_DATABASE_NAME', COUCH_DB_DEFAULT)
    couch_data_file = os.path.join(COUCH_DATA_DIR, '%s.couch' % couch_db)
    paranoid_restore(os.path.join(backup_dir, 'db.couch'), couch_data_file, sudo)
    sudo('chown %s:%s "%s"' % (COUCH_USER, COUCH_USER, couch_data_file))

    _print('re-indexing couch views (may take a while...)')
    _start_couchdb()
    with cd(APP_DIR):
        fab_bhoma.reindex_views()
        pass

    _print("""
  the upgrade and restore is complete. next steps:

  0) verify no errors occurred during the restore; if they did, contact a data
     team member and don't deploy this server

  1) the current system time is %s. set the correct time
     if this is wrong

  2) reboot the server

  3) perform the post-upgrade testing and verification steps
""" % clock_str())

def _print(text, err=False):
    colorize = colors.red if err else colors.yellow
    print colorize(text)

@contextmanager
def postgres_op():
    engine = get_django_setting('DATABASE_ENGINE', 'postgresql_psycopg2')
    dbname = get_django_setting('DATABASE_NAME', 'bhoma')
    dbuser = get_django_setting('DATABASE_USER', 'bhoma')
    dbpass = get_django_setting('DATABASE_PASSWORD')
    if dbpass is None:
        dbpass = prompt('postgres db password:')

    if not engine.startswith('postgres'):
        raise Exception('postgres ops can only be performed in a postgres environment')

    # note: tmpfile is local only; will break for a remote server
    fd, tmpfile = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as f:
        f.write('*:*:*:%s:%s\n' % (dbuser, dbpass))
        
    def pgrun(cmd):
        run('export PGPASSFILE=%s && %s' % (tmpfile, dbname.join(cmd.split('{{db}}'))))
    yield pgrun

    os.remove(tmpfile)

def norm_dstfile(dstfile, srcfile):
    if os.path.isdir(dstfile):
        return os.path.join(dstfile, os.path.split(srcfile)[1])
    else:
        return dstfile

def hashfile(path, runcmd):
    return runcmd('sha1sum "%s"' % path)[:40]

def paranoid_backup(srcfile, dstfile, runcmd=run):
    """for copying a file to a device you don't trust the integrity of"""
    dstfile = norm_dstfile(dstfile, srcfile)

    srchash = hashfile(srcfile, runcmd)
    runcmd('cp "%s" "%s"' % (srcfile, dstfile))
    dsthash = hashfile(dstfile, runcmd)

    if srchash != dsthash:
        _print('file [%s] did not copy successfully; it is corrupted on the external drive/memory card!' % srcfile, True)
        sys.exit()

    runcmd('echo %s > "%s.chksum"' % (dsthash, dstfile))

def paranoid_restore(srcfile, dstfile, runcmd=run):
    """for restoring a file from a device you don't trust the integrity
    of (relies on the checksum file from paranoid_backup)"""
    dstfile = norm_dstfile(dstfile, srcfile)
    
    srchash = runcmd('cat "%s.chksum"' % srcfile)[:40]
    runcmd('cp "%s" "%s"' % (srcfile, dstfile))
    dsthash = hashfile(dstfile, runcmd)

    if srchash != dsthash:
        _print('file [%s] did not copy successfully; it is corrupted on the external drive/memory card!' % dstfile, True)
        sys.exit()

