from django.test.simple import DjangoTestSuiteRunner
from django.conf import settings
from couchdbkit.ext.django import loading as loading
from couchdbkit.resource import ResourceNotFound
from dimagi.utils.couch.testrunner import CouchDbKitTestSuiteRunner
from bhoma import settingshelper

class BhomaTestSuiteRunner(CouchDbKitTestSuiteRunner):
    """
    A test suite runner for bhoma.  On top of the couchdb testrunner, also
    apply all our monkeypatches to the settings.
    
    To use this, change the settings.py file to read:
    
    TEST_RUNNER = 'bhoma.testrunner.BhomaTestSuiteRunner'
    """
    
    dbs = []
    
    def setup_databases(self, **kwargs):
        returnval = super(BhomaTestSuiteRunner, self).setup_databases(**kwargs)
        self.newdbname = self.get_test_db_name(settings.COUCH_DATABASE_NAME)
        print "overridding the couch settings!"
        new_db_settings = settingshelper.get_dynamic_db_settings(settings.COUCH_SERVER_ROOT, 
                                                                 settings.COUCH_USERNAME, 
                                                                 settings.COUCH_PASSWORD, 
                                                                 self.newdbname, 
                                                                 settings.INSTALLED_APPS)
        settings.COUCH_DATABASE_NAME = self.newdbname
        for (setting, value) in new_db_settings.items():
            setattr(settings, setting, value)
            print "set %s settting to %s" % (setting, value)
        # hack - set the other values too
        return returnval
