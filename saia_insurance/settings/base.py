"""
إعدادات Django الأساسية المشتركة
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,concord-saia.bineyes.com,www.concord-saia.bineyes.com').split(',')

# Base URL for generating full links
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8000')

# CSRF Settings for domain
CSRF_TRUSTED_ORIGINS = [
    'https://concord-saia.bineyes.com',
    'https://www.concord-saia.bineyes.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000'
]

# Session Cookie Settings
SESSION_COOKIE_SECURE = os.getenv('DJANGO_ENV', 'development') == 'production'
CSRF_COOKIE_SECURE = os.getenv('DJANGO_ENV', 'development') == 'production'
SECURE_SSL_REDIRECT = False  # Nginx handles SSL
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    # 'django_ai_assistant',  # تعطيل مؤقتاً - سيتم تفعيله بعد التثبيت
    # 'ninja',  # تعطيل مؤقتاً
    'rest_framework',  # Django REST Framework
    
    # Local apps
    'insurance_core.apps.InsuranceCoreConfig',
    'insurance_ai.apps.InsuranceAiConfig',
    'whatsapp_integration.apps.WhatsappIntegrationConfig',
    'payments.apps.PaymentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # تعطيل مؤقتاً
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'saia_insurance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # إضافة مجلد templates
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

WSGI_APPLICATION = 'saia_insurance.wsgi.application'

# Database
# التحويل إلى PostgreSQL للإنتاج (أفضل مع concurrent access)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'saia_insurance'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'saia_secure_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # إعادة استخدام الاتصالات
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# SQLite للتطوير المحلي (اختياري - يمكن تفعيله بتغيير USE_SQLITE=True في .env)
if os.getenv('USE_SQLITE', 'False').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 30,
            }
        }
    }
    # تفعيل WAL mode لـ SQLite
    def configure_sqlite_wal():
        import sqlite3
        db_path = BASE_DIR / 'db.sqlite3'
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA busy_timeout=30000;")
                conn.close()
            except Exception:
                pass
    configure_sqlite_wal()

# PostgreSQL Configuration (للإنتاج)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#         'CONN_MAX_AGE': 600,
#         'OPTIONS': {
#             'connect_timeout': 10,
#         }
#     }
# }

# MongoDB Configuration
MONGODB_SETTINGS = {
    'URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
    'DB_NAME': os.getenv('MONGODB_DB_NAME', 'saia_sessions'),
}

# Redis URL for context storage
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')

# Cache Configuration (تعطيل Redis مؤقتاً - استخدام ذاكرة محلية)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'saia-cache',
    }
}

# Redis Cache (للإنتاج)
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         },
#         'KEY_PREFIX': 'saia',
#         'TIMEOUT': 3600,
#     }
# }

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Riyadh'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Enable for serving static files
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # تعطيل مؤقتاً

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'insurance_core.User'

# Base URL for API responses (used for PDF links, etc.)
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8222')

# AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Google Gemini API Key

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')

# Payment Gateways
MOYASAR_API_KEY = os.getenv('MOYASAR_API_KEY')
HYPERPAY_ACCESS_TOKEN = os.getenv('HYPERPAY_ACCESS_TOKEN')

# Django AI Assistant
AI_ASSISTANT_CAN_RUN_ASSISTANT = "insurance_ai.permissions.can_run_insurance_assistant"

# Logging
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
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'saia.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'insurance_ai': {'handlers': ['console', 'file'], 'level': 'DEBUG'},
    },
}
