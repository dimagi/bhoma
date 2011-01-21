from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from bhoma.utils.couch.database import get_db
from bhoma.utils.logging import log_exception
import logging
from datetime import datetime
from bhoma.logconfig import init_file_logging
from bhoma.utils.parsing import string_to_boolean
from bhoma.apps.patient.management.commands.shared import are_you_sure
import sys
from couchdbkit.resource import ResourceNotFound
from optparse import make_option
from couchdbkit.client import Database
from distutils.version import LooseVersion
from bhoma.apps.webapp.config import get_current_site, is_clinic

class SettingsConfig(object):
    DATABASE = "DATABASE_NAME"
    COUCH_DB = "BHOMA_COUCH_DATABASE_NAME"
    NATIONAL_DB = "BHOMA_NATIONAL_DATABASE_NAME"
    NATIONAL_SERVER = "BHOMA_NATIONAL_SERVER_ROOT"
    CACHE_BACKEND = "CACHE_BACKEND" 
    DEBUG = "DEBUG" 

_PROPER_CONFIG = {"rev2": {SettingsConfig.DATABASE: "bhoma",
                           SettingsConfig.COUCH_DB: "bhoma",
                           SettingsConfig.NATIONAL_DB: "bhoma_production", 
                           SettingsConfig.NATIONAL_SERVER: "bhoma.cidrz.org:5984",
                           SettingsConfig.CACHE_BACKEND: "memcached://127.0.0.1:11211/",
                           SettingsConfig.DEBUG: False}
                  }
def _version_from_settings():
    v = LooseVersion(settings.BHOMA_APP_VERSION)
    if LooseVersion("0.2.0") <= v < LooseVersion("0.3.0"):
        return "rev2"
    else:
        return "unknown"
        
    
class Info(object):
    def __init__(self, param, value):
        self.param = param
        self.value = value
    
    def __str__(self):
        return "%(param)s: %(value)s" % {"param": self.param, "value": self.value} 
    
    
class TestResult(object):
    
    def __init__(self, param, expected, actual):
        self.param = param
        self.expected = expected
        self.actual = actual
    
    def passed(self):
        return self.expected == self.actual
    
    def __str__(self):
        if self.passed():
            return "checked %(param)s ... %(actual)s [ok]" % {"param": self.param, "actual": self.actual} 
        else:
            return "checked %(param)s ... expected %(expected)s but was %(actual)s [FAIL]" %\
                    {"param": self.param, "expected": self.expected, "actual": self.actual} 

     
class Command(LabelCommand):
    help = "Checks the bhoma configuration."
    args = "version"
    label = ""
    
    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError('Usage: manage.py check_config')
        
        version = _version_from_settings()
        if version not in _PROPER_CONFIG:
            raise CommandError('Bad or unknown version of software!')
        
        results = []
        info = []
        config = _PROPER_CONFIG[version]
        for key, val in config.items():
            results.append(TestResult(key, val, getattr(settings, key, "")))
        results.append(TestResult("current site is clinic", True, is_clinic()))
        
        info.append(Info("CLINIC", get_current_site()))
        info.append(Info("BHOMA_APP_VERSION", settings.BHOMA_APP_VERSION))
        info.append(Info("BHOMA_COMMIT_ID", settings.BHOMA_COMMIT_ID))
        
        print ""
        print "Configuration information:"
        for item in info:
            print item
        print ""
        print ""
        print "Configuration Test Results:"
        failed = False
        for item in results:
            print item
            failed = failed or not item.passed()
        
        print ""
        print ""
        if failed:
            print "Overall check: [FAIL].  Double check settings in localsettings.py!"
        else:
            print "Overall check [ok]. Hooray!"