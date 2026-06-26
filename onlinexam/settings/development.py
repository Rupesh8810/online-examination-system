from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable CSRF for development convenience (re-enable in prod)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
