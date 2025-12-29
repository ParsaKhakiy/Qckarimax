"""
Development settings
"""
from .base import *

DEBUG = True

# Development-specific middleware
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development database (can use SQLite for local dev)
# DATABASES['default'] = {
#     'ENGINE': 'django.db.backends.sqlite3',
#     'NAME': BASE_DIR / 'db.sqlite3',
# }

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

