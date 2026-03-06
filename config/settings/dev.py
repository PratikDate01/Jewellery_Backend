import os
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# ========================
# DATABASE (MongoDB)
# ========================

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_backend',
        'NAME': 'jewellery_db',
        'ENFORCE_SCHEMA': False,
        'HOST': os.getenv('MONGO_URI'),
    }
}

# ========================
# CORS SETTINGS
# ========================

CORS_ALLOW_ALL_ORIGINS = True

# ========================
# LOGGING
# ========================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'pymongo': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'djongo': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
