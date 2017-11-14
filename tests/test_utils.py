from unittest.mock import MagicMock, patch

from django.test import TestCase

from django_orghierarchy.utils import get_data_source_model, swapper
from django_orghierarchy.models import DataSource


class TestGetDataSourceModel(TestCase):

    def test_get_data_source_model_return_default_model(self):
        model = get_data_source_model()
        self.assertIs(model, DataSource)

    @patch('swapper.load_model', MagicMock())
    def test_get_data_source_model_swapper_load_model_called(self):
        get_data_source_model()
        self.assertTrue(swapper.load_model.called)
