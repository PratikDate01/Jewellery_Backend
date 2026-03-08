import cloudinary
from pathlib import Path
import os
from dotenv import load_dotenv

import sys
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from backend root
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ========================
# SECURITY SETTINGS
# ========================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this')

DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# In production, this should be set to your actual domain
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'jewellery-backend-ewfw.onrender.com,localhost,127.0.0.1').split(',')


# ========================
# INSTALLED APPS
# ========================

INSTALLED_APPS = [
    # Default Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Apps
    'cloudinary',
    'cloudinary_storage',
    'rest_framework',
    'corsheaders',
    'django_filters',

    # Local Apps
    'accounts',
    'products',
    'categories',
    'cart',
    'wishlist',
    'orders',
    'payments',
    'reviews',
    'suppliers',
    'wholesale',
    'coupons',
    'analytics',
]


# ========================
# MIDDLEWARE
# ========================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


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
# AUTHENTICATION
# ========================

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

import datetime

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'accounts.renderers.MongoJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

ADMIN_EMAILS = [
    'admin@jewellery.com',
    'superadmin@jewellery.com',
]



# ========================
# PASSWORD VALIDATION
# ========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ========================
# INTERNATIONAL SETTINGS
# ========================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True


# ========================
# STATIC & MEDIA FILES
# ========================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ========================
# CORS SETTINGS (React)
# ========================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://jwellery-frontend-opal.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if os.getenv('EXTRA_CORS_ORIGINS'):
    CORS_ALLOWED_ORIGINS.extend(os.getenv('EXTRA_CORS_ORIGINS').split(','))

CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

CSRF_TRUSTED_ORIGINS = [
    'https://jwellery-frontend-opal.vercel.app',
    'https://jewellery-backend-ewfw.onrender.com',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Security Hardening
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
    X_FRAME_OPTIONS = 'DENY'
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_FAILURE_VIEW = 'rest_framework.exceptions.invalid_request'


# ========================
# THIRD PARTY INTEGRATIONS
# ========================

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME','dpxb4gf5m'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY','612981162734986'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET','FEN2xeA7akzEbkj4NYDRl-YkxBs'),
    'SECURE': True,
}

# Ensure Cloudinary SDK also uses HTTPS
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Max upload size configuration
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024 # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024 # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

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
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


# ========================
# DEFAULT PRIMARY KEY
# ========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
