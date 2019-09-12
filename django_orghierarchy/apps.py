from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoOrghierarchyConfig(AppConfig):
    name = 'django_orghierarchy'
    verbose_name = _('Organizations')
