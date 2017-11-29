from django.contrib import admin
from django.test import TestCase, tag

from django_orghierarchy.utils import get_data_source_model
from django_orghierarchy.models import DataSource, Organization
from ..models import CustomPrimaryKeyDataSource


@tag('custom_pk_ds')
class TestCustomPrimaryKeyDataSource(TestCase):

    def test_get_data_source_model(self):
        model = get_data_source_model()
        self.assertIs(model, CustomPrimaryKeyDataSource)

    def test_related_data_source_model(self):
        field = Organization._meta.get_field('data_source')
        self.assertIs(field.related_model, CustomPrimaryKeyDataSource)

    def test_default_data_source_admin_not_registered(self):
        is_registered = admin.site.is_registered(DataSource)
        self.assertFalse(is_registered)
