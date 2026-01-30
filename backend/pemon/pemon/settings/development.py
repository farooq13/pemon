"""
Development-specific settings for Pemon Fintech Platform.

These settings are used during local development.
DO NOT use these settings in production.
"""

from .base import *

# DEBUG SETTINGS

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']


# INSTALLED APPS - Development Only

INSTALLED_APPS += [
    'django_extensions',  # Useful development tools
    'debug_toolbar',  # Django Debug Toolbar for performance profiling
]


# MIDDLEWARE - Development Only

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]


# DEBUG TOOLBAR CONFIGURATION

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}


# DATABASE - Development

# Use the default database configuration from base.py
# Add query logging for development
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}


# EMAIL - Development (Console Backend)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# CORS - Development (Allow all origins for local development)

CORS_ALLOW_ALL_ORIGINS = True


# REST FRAMEWORK - Development

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API
)


# SECURITY - Development (Relaxed for local development)

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# CACHING - Development (Use dummy cache for easier debugging)

# Uncomment to disable caching during development
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }


# CELERY - Development

# Always eager mode for easier debugging (tasks run synchronously)
# Uncomment if you want to test without running Celery worker
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True


# DEVELOPMENT TOOLS

# Shell Plus Configuration
SHELL_PLUS = "ipython"

SHELL_PLUS_PRINT_SQL = True

# Show SQL queries in shell
SHELL_PLUS_POST_IMPORTS = [
    ('django.db', 'connection'),
]


# LOGGING - Development (Verbose logging)

LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['root']['level'] = 'DEBUG'

