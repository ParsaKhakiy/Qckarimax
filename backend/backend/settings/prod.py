"""
Production settings
"""
from .base import *

DEBUG = False

# Security settings for production
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Production logging
LOGGING['handlers']['file']['filename'] = '/var/log/payment/payment.log'

BASE_URL_SWAGGER = 'swagger'