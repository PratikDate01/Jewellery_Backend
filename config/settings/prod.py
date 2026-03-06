from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [host for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host]

# ========================
# DATABASE (MongoDB Atlas)
# ========================

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_backend',
        'NAME': 'jewellery_db',
        'ENFORCE_SCHEMA': False,
        'HOST': os.getenv('MONGO_URI'),
    }
}

# Static files optimization for production
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ========================
# SECURITY HARDENING
# ========================

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ========================
# CORS SETTINGS
# ========================

CORS_ALLOWED_ORIGINS = [origin for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin]
CORS_ALLOW_CREDENTIALS = True

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
