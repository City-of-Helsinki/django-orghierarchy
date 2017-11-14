from django.test import TestCase, tag

from django_orghierarchy import get_data_source_model
from django_orghierarchy.models import Organization
from ..models import CustomDataSource


@tag('custom_ds')
class TestCustomDataSource(TestCase):

    def test_get_data_source_model(self):
        model = get_data_source_model()
        self.assertIs(model, CustomDataSource)

    def test_related_data_source_model(self):
        field = Organization._meta.get_field('data_source')
        self.assertIs(field.related_model, CustomDataSource)
