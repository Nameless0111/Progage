from .settings import *
import os

# Shared hosting settings (Timeweb)
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Database for cloud deployment (PostgreSQL)
# Используй переменные окружения или раскомментируй и заполни напрямую

if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='progage_db'),
            'USER': config('DB_USER', default='progage_user'),
            'PASSWORD': config('DB_PASSWORD', default='1111'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Для MySQL/MariaDB (если хостинг не поддерживает PostgreSQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'имя_БД',  # Замени на имя базы данных
#         'USER': 'имя_пользователя_БД',  # Замени на имя пользователя
#         'PASSWORD': 'пароль',  # Замени на пароль от базы данных
#         'HOST': 'localhost',  # Для Timeweb всегда localhost
#         'PORT': '3306',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

# Static files for shared hosting
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files for shared hosting
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
MEDIA_URL = '/media/'

# Email settings for shared hosting
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.timeweb.ru'  # Timeweb SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@your-domain.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-email-password')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@your-domain.com')

# Security settings for shared hosting
SECURE_SSL_REDIRECT = False  # Может не работать на shared hosting
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging for shared hosting
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
