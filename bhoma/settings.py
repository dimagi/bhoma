# Django settings for bhoma project.
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

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
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

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
    'couchdbkit.ext.django',
    "bhoma.contrib.django_digest",
    "bhoma.apps.webapp",
    "bhoma.apps.djangocouch",
    "bhoma.apps.case",
    "bhoma.apps.chw",
    "bhoma.apps.couchlog",
    "bhoma.apps.drugs",
    "bhoma.apps.encounter",
    #"bhoma.apps.erlang",
    "bhoma.apps.export",
    "bhoma.apps.locations",
    "bhoma.apps.patient",
    "bhoma.apps.phone",
    "bhoma.apps.phonelog",
    "bhoma.apps.profile",
    "bhoma.apps.reports",
    "bhoma.apps.xforms",
    "bhoma.apps.zscore",
        
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
BHOMA_NATIONAL_SERVER_ROOT = "bhoma.cidrz.org"
BHOMA_NATIONAL_DATABASE_NAME = "national"
# If authentication is required, fill these in
BHOMA_NATIONAL_USERNAME = ""
BHOMA_NATIONAL_PASSWORD = ""

# Bhoma config

BHOMA_CLINIC_ID = "CHANGE_ME" # change to your clinic code: e.g. "5020280" for Kafue Railway

# xforms stuff

XFORMS_PATH = "data/xforms"
XFORMS_FORM_BOOTSTRAP_PATH = "xforms" # where your auto-bootstrapped forms live
XFORMS_PLAYER_URL = "http://localhost:444/"

# email settings go here, if you want your server to be able to send emails
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "<your username>@gmail.com"
EMAIL_HOST_PASSWORD = "<password>"
EMAIL_USE_TLS = True

# the default address that support emails go to
BHOMA_SUPPORT_EMAIL = "yourname@project.com"
BHOMA_APP_VERSION = "0.2.0dev"

MANAGEMENT_COMMAND_LOG_FILE="/var/log/bhoma/bhoma_mgmt.log"
LUCENE_ENABLED = False # use lucene for search

BHOMA_TMP_DIR = '/var/lib/bhoma' #data should persist across reboots, ruling out /tmp

TABS = [
    ("bhoma.apps.reports.views.report_list", "Reports"),
    ("bhoma.apps.chw.views.list_chws", "CHWs"),
    ("bhoma.apps.patient.views.dashboard", "Patients", "superuser"),
    ("bhoma.apps.patient.views.export_data", "Export Data", "superuser"),
    ("bhoma.apps.couchlog.views.dashboard", "Errors", "superuser"),
]

# load our settings mid-file so they can override some properties
try:
    from localsettings import *
except ImportError:
    pass

from settingshelper import get_server_url, get_dynamic_db_settings, get_commit_id

BHOMA_COMMIT_ID = get_commit_id()
_dynamic_db_settings = get_dynamic_db_settings(BHOMA_COUCH_SERVER_ROOT, BHOMA_COUCH_USERNAME, BHOMA_COUCH_PASSWORD, BHOMA_COUCH_DATABASE_NAME, INSTALLED_APPS)

# create local server and database configs
BHOMA_COUCH_SERVER = _dynamic_db_settings["BHOMA_COUCH_SERVER"]
BHOMA_COUCH_DATABASE = _dynamic_db_settings["BHOMA_COUCH_DATABASE"]

# create couch app database references
COUCHDB_DATABASES = _dynamic_db_settings["COUCHDB_DATABASES"]

# other urls that depend on the server 
XFORMS_POST_URL = _dynamic_db_settings["XFORMS_POST_URL"]

# create national server and database configs
BHOMA_NATIONAL_SERVER = get_server_url(BHOMA_NATIONAL_SERVER_ROOT,
                                       BHOMA_NATIONAL_USERNAME,
                                       BHOMA_NATIONAL_PASSWORD)

BHOMA_NATIONAL_DATABASE = "%(server)s/%(database)s" % \
    {"server": BHOMA_NATIONAL_SERVER, "database": BHOMA_NATIONAL_DATABASE_NAME }


