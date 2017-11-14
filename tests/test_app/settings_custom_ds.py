from ..settings import *  # noqa

INSTALLED_APPS = INSTALLED_APPS + ['tests.test_app']  # noqa

DJANGO_ORGHIERARCHY_DATASOURCE_MODEL = 'test_app.CustomDataSource'
