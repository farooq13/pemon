"""
Settings module initialization.

Loads the appropriate settings module based on DJANGO_SETTINGS_MODULE environment variable.
Defaults to development settings if not specified.
"""

import os

from decouple import config

# Determine which settings module to use
settings_module = config('DJANGO_SETTINGS_MODULE', default='pemon.settings.development')

# Extract just the final part (development or production)
environment = settings_module.split('.')[-1]

