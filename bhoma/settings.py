
DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ("127.0.0.1", "localhost")

TEST_RUNNER = 'bhoma.testrunner.BhomaTestSuiteRunner'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/var/src/bhoma/bhoma/data/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 't@x8944rd@6!ya-r_+321$*2mlx(mfyohioxeczh5r+^-gc2f2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = ( 
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "bhoma.context_processors.webapp",
    "couchlog.context_processors.static_workaround",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'bhoma.middleware.LogExceptionsMiddleware',
    'bhoma.middleware.LoginRequiredMiddleware',
    'bhoma.middleware.ConfigurationCheckMiddleware',
)

ROOT_URLCONF = 'bhoma.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'couchdbkit.ext.django',
    "couchversion",
    "djangocouch",
    "couchlog",
    "bhoma.contrib.django_digest",
    "bhoma.apps.webapp",
    "bhoma.apps.case",
    "bhoma.apps.centralreports",
    "bhoma.apps.chw",
    "bhoma.apps.bhomalog",
    "bhoma.apps.drugs",
    "bhoma.apps.encounter",
    #"bhoma.apps.erlang",
    "bhoma.apps.export",
    "bhoma.apps.locations",
    "bhoma.apps.migration",
    "bhoma.apps.patient",
    "bhoma.apps.phone",
    "bhoma.apps.phonelog",
    "bhoma.apps.profile",
    "bhoma.apps.reports",
    "bhoma.apps.xforms",
    "bhoma.apps.zones", 
    "bhoma.apps.zscore",
    "touchforms.formplayer",
)

# after login, django redirects to this URL
# rather than the default 'accounts/profile'
LOGIN_REDIRECT_URL='/'
LOGIN_URL='/accounts/login/'

AUTH_PROFILE_MODULE = "profile.BhomaUserProfile"


# Override the default log settings
LOG_LEVEL = "WARN"
LOG_FILE = "/var/log/bhoma/bhoma.log"
DJANGO_LOG_FILE = "/var/log/bhoma/bhoma.django.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
LOG_SIZE = 1000000 # in bytes
LOG_BACKUPS = 256     # number of logs to keep around

# this is how we configure couchdbkit's django extensions to point at
# our couch db
BHOMA_COUCH_SERVER_ROOT   = "localhost:5984"
BHOMA_COUCH_DATABASE_NAME = "bhoma"
# If authentication is required, fill these in
BHOMA_COUCH_USERNAME = ""
BHOMA_COUCH_PASSWORD = ""

DJANGO_SERVE_STATIC_MEDIA = True

# national database configuration - where this install syncs to
BHOMA_NATIONAL_SERVER_ROOT = "bhoma.cidrz.org:5984"
BHOMA_NATIONAL_DATABASE_NAME = "bhoma_production"
# If authentication is required, fill these in
BHOMA_NATIONAL_USERNAME = ""
BHOMA_NATIONAL_PASSWORD = ""

REPLICATE_THROUGH_SSH_TUNNEL = False
REPLICATE_TUNNEL_PORT = 6984

# Bhoma config

BHOMA_CLINIC_ID = "CHANGE_ME" # change to your clinic code: e.g. "5020280" for Kafue Railway

# xforms stuff

XFORMS_PATH = "data/xforms"
XFORMS_BOOTSTRAP_PATH = "xforms" # where your auto-bootstrapped forms live
XFORMS_PLAYER_URL = "http://localhost:444/"

# email settings go here, if you want your server to be able to send emails
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "<your username>@gmail.com"
EMAIL_HOST_PASSWORD = "<password>"
EMAIL_USE_TLS = True

# the default address that support emails go to
SUPPORT_EMAIL = "bhoma-support@dimagi.com"
APP_VERSION = "0.2.3"

# shutdown settings
BHOMA_CAN_POWER_DOWN_SERVER = True # what it sounds like
SHUTDOWN_DELAY = 2.
SHUTDOWN_BUFFER = 30.
SHUTDOWN_TIMEOUT = 120.


MANAGEMENT_COMMAND_LOG_FILE="/var/log/bhoma/bhoma_mgmt.log"
LUCENE_ENABLED = False # use lucene for search

BHOMA_TMP_DIR = '/var/lib/bhoma' #data should persist across reboots, ruling out /tmp

TABS = [
    ("bhoma.apps.reports.views.report_list", "Reports"),
    ("bhoma.apps.chw.views.list_chws", "CHWs", "superuser"),
    ("bhoma.apps.patient.views.dashboard", "Patients", "superuser"),
    ("bhoma.apps.patient.views.export_data", "Export Data", "superuser"),
    ("couchlog.views.dashboard", "Errors", "superuser"),
]


# couchlog config
COUCHLOG_TABLE_CONFIG = {"id_column":       0,
                         "archived_column": 1,
                         "date_column":     3,
                         "message_column":  5,
                         "actions_column":  7,
                         "email_column":    8,
                         "no_cols":         9}

COUCHLOG_DISPLAY_COLS = ["id", "archived?", "clinic", "date", "exception type", "message", "url (if applicable)", "actions", "report"]
COUCHLOG_RECORD_WRAPPER = "bhoma.apps.bhomalog.wrapper"
COUCHLOG_LUCENE_VIEW = "bhomalog/search" 
COUCHLOG_LUCENE_DOC_TEMPLATE = "bhomalog/lucene_docs.html"

COUCHLOG_JQUERY_LOC = "%s%s" % (MEDIA_URL, "webapp/javascripts/jquery-1.4.2.min.js")
COUCHLOG_JQUERYUI_LOC = "%s%s" % (MEDIA_URL, "webapp/javascripts/jquery-ui-1.8.5.custom.min.js")
COUCHLOG_JQUERYUI_CSS_LOC = "%s%s" % (MEDIA_URL, "webapp/stylesheets/jquery-ui-smoothness/jquery-ui-1.8.5.custom.css")
COUCHLOG_JQMODAL_LOC = "%s%s" % (MEDIA_URL, "webapp/javascripts/jqModal.js")
COUCHLOG_JQMODAL_CSS_LOC = "%s%s" % (MEDIA_URL, "webapp/stylesheets/jqModal.css")
COUCHLOG_DATATABLES_LOC = "%s%s" % (MEDIA_URL, "webapp/datatables/js/jquery.dataTables.min.js")
COUCHLOG_BLUEPRINT_HOME = "%s%s" % (MEDIA_URL, "webapp/stylesheets/blueprint/")

# load our settings mid-file so they can override some properties
try:
    from localsettings import *
except ImportError:
    pass

from settingshelper import get_server_url, get_server_domain, get_dynamic_db_settings

_dynamic_db_settings = get_dynamic_db_settings(BHOMA_COUCH_SERVER_ROOT, BHOMA_COUCH_USERNAME, 
                                               BHOMA_COUCH_PASSWORD, BHOMA_COUCH_DATABASE_NAME, 
                                               INSTALLED_APPS, BHOMA_CLINIC_ID)

# create local server and database configs
BHOMA_COUCH_SERVER = _dynamic_db_settings["BHOMA_COUCH_SERVER"]
BHOMA_COUCH_DATABASE = _dynamic_db_settings["BHOMA_COUCH_DATABASE"]

# create couch app database references
COUCHDB_DATABASES = _dynamic_db_settings["COUCHDB_DATABASES"]

# other urls that depend on the server 
XFORMS_POST_URL = _dynamic_db_settings["XFORMS_POST_URL"]

# create national server and database configs
BHOMA_NATIONAL_SERVER = get_server_url(get_server_domain(BHOMA_NATIONAL_SERVER_ROOT,
                                                         REPLICATE_THROUGH_SSH_TUNNEL,
                                                         REPLICATE_TUNNEL_PORT),
                                       BHOMA_NATIONAL_USERNAME,
                                       BHOMA_NATIONAL_PASSWORD)
BHOMA_NATIONAL_DATABASE = "%(server)s/%(database)s" % \
    {"server": BHOMA_NATIONAL_SERVER, "database": BHOMA_NATIONAL_DATABASE_NAME }

import os.path
BHOMA_ROOT_DIR = os.path.normpath(os.path.dirname(__file__))

from dimagi.utils.repo import get_revision
BHOMA_COMMIT_ID = get_revision('git', BHOMA_ROOT_DIR)

TOUCHFORMS_ABORT_DEST = 'landing_page'
TOUCHFORMS_AUTOCOMPL_DATA_DIR = os.path.join(BHOMA_ROOT_DIR, 'static')
TOUCHFORMS_AUTOCOMPL_DYNAMIC_LOADER = 'bhoma.utils.autocomplete.couch_loader'
TOUCHFORMS_AUTOCOMPL_CONFIGURATOR = 'bhoma.utils.autocomplete.get_config'

#new submodule compatibility
COUCH_DATABASE_NAME = BHOMA_COUCH_DATABASE_NAME
COUCH_DATABASE = BHOMA_COUCH_DATABASE
COUCH_SERVER = BHOMA_COUCH_SERVER
COUCH_SERVER_ROOT = BHOMA_COUCH_SERVER_ROOT
COUCH_USERNAME = BHOMA_COUCH_USERNAME
COUCH_PASSWORD = BHOMA_COUCH_PASSWORD

