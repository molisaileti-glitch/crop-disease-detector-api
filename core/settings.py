# core/settings.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Django configuration file.
# All sensitive values are read from .env file
# using decouple — never hardcoded here.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from pathlib import Path
from decouple import config
from datetime import timedelta
#import sentry_sdk
import dj_database_url

# ── BASE DIRECTORY ──────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── SECURITY ────────────────────────────────────────
# Read secret key from .env — never hardcode this
SECRET_KEY = config('SECRET_KEY')

# Read debug from .env — False in production
DEBUG = config('DEBUG', default=False, cast=bool)

# Read allowed hosts from .env
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1'
).split(',')

# ── INSTALLED APPS ───────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',           # Django REST Framework
    'rest_framework_simplejwt', # JWT authentication
    'corsheaders',              # Allow Flutter to call API
    'cloudinary',               # Image storage
    'cloudinary_storage',       # Cloudinary integration
    'drf_yasg',                 # Swagger API docs

    # Our apps
    'api',
    'ml',
]
# Tell Django to use our custom User model
AUTH_USER_MODEL = 'api.User'

# ── MIDDLEWARE ───────────────────────────────────────
MIDDLEWARE = [
    # CORS must be first
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ── TEMPLATES ────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── DATABASE ─────────────────────────────────────────
# Reads DATABASE_URL from .env
# Locally: sqlite:///db.sqlite3
# On Render: postgresql://... (Render provides this)
DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# ── PASSWORD VALIDATION ──────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNATIONALIZATION ─────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Dar_es_Salaam'
USE_I18N      = True
USE_TZ        = True

# ── STATIC FILES ─────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── MEDIA FILES ──────────────────────────────────────
# Used locally — on production Cloudinary handles this
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── CLOUDINARY ───────────────────────────────────────
# Image storage — all uploaded images go to Cloudinary
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ── DJANGO REST FRAMEWORK ────────────────────────────
REST_FRAMEWORK = {
    # Require JWT authentication by default
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Require authentication for all endpoints by default
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Limit API responses to prevent abuse
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',    # anonymous users
        'user': '100/day',    # authenticated users
    }
}

# ── JWT SETTINGS ─────────────────────────────────────
SIMPLE_JWT = {
    # Token expires after 24 hours
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=24),
    # Refresh token lasts 7 days
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'ALGORITHM':              'HS256',
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

# ── CORS ─────────────────────────────────────────────
# Allow Flutter app to call our API
# In production replace with your actual domain
CORS_ALLOW_ALL_ORIGINS = DEBUG  # True in dev, False in prod
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:8000',
]

# ── SENTRY ERROR MONITORING ──────────────────────────
#SENTRY_DSN = config('SENTRY_DSN', default='')
#if SENTRY_DSN:
    #sentry_sdk.init(
        #dsn=SENTRY_DSN,
        # Capture 100% of errors
        #traces_sample_rate=1.0,
    #)

# ── IMAGE UPLOAD SETTINGS ────────────────────────────
# Max image size: 2MB
MAX_UPLOAD_SIZE = 2 * 1024 * 1024
# Allowed image types
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
# Min and max image dimensions
MIN_IMAGE_DIMENSION = 100
MAX_IMAGE_DIMENSION = 4000

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Static files with whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'