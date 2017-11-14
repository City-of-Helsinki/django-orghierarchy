DEBUG = True
USE_TZ = True

SECRET_KEY = '00000000000000000000000000000000000000000000000000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django_orghierarchy',
]
