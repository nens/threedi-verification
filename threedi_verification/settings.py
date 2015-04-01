# Production settings, but don't put passwords in here.
# Secret key: in localproductionsettings.py

import os


SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
TESTCASES_ROOT = os.path.join(BUILDOUT_DIR, 'testbank')
URBAN_TESTCASES_ROOT = os.path.join(BUILDOUT_DIR, 'testbank_urban')
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
STATIC_URL = '/testresults/static/'
ROOT_URLCONF = 'threedi_verification.urls'

SECRET_KEY = 'sleutel van het secreet'
DEBUG = True
ALLOWED_HOSTS = ['jenkins.3di.lizard.net', 'localhost']
TEMPLATE_DEBUG = True
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BUILDOUT_DIR, 'var/db/verification.db')},
}
INSTALLED_APPS = [
    'threedi_verification',
    'south',
    'gunicorn',
    #'debug_toolbar',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_nose',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
]
# MIDDLEWARE_CLASSES = (
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
#     # Default stuff below.
#     'django.middleware.common.CommonMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     # Defaults above, extra two below.
#     # 'trs.middleware.TracebackLoggingMiddleware',
#     'tls.TLSRequestMiddleware',
# )

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

STATICFILES_DIRS = [
    os.path.join(BUILDOUT_DIR, 'bower_components'),
    # ^^^ bower-managed files.
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)s %(levelname)s\n    %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BUILDOUT_DIR,
                                     'var', 'log', 'django.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['console', 'logfile'],
            'propagate': False,
            'level': 'ERROR',  # WARN also shows 404 errors
        },
    }
}

USE_L10N = True
USE_I18N = True
LANGUAGE_CODE = 'nl-nl'
TIME_ZONE = 'Europe/Amsterdam'

INTERNAL_IPS = ['localhost', '127.0.0.1']

# Libraries (probably) only checked for timestamp
SUBGRID_LIBRARY_LOCATION = '/opt/3di/bin/subgridf90'
FLOW_LIBRARY_LOCATION = '/opt/threedicore/bin/flow1d2d'


try:
    from .localsettings import *
except ImportError:
    pass
