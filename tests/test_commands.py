from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from django_orghierarchy.importers import DataImportError
from django_orghierarchy.models import Organization, OrganizationClass
from django_orghierarchy.utils import get_data_source_model
from .test_importers import mock_request_get


class TestRestImportCommand(TestCase):

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_rest_import(self):
        url = 'http://fake.url/organizations/?page=1'
        call_command('rest_import', url)

        data_source_model = get_data_source_model()
        self.assertEqual(Organization.objects.count(), 3)
        self.assertEqual(data_source_model.objects.count(), 2)
        self.assertEqual(OrganizationClass.objects.count(), 2)

        url = 'http://not-exist.url/organizatoins/?page=1'
        try:
            call_command('rest_import', url)
        except DataImportError:
            self.fail('The command does not handle DataImportError')
