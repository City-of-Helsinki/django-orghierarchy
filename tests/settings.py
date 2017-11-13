import django

DEBUG = True
USE_TZ = True

SECRET_KEY = "00000000000000000000000000000000000000000000000000"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "django-orghierarchy",
    }
}

INSTALLED_APPS = [
    "django_orghierarchy",
]
