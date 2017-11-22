from unittest.mock import MagicMock, patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from django_orghierarchy.importers import DataImportError
from django_orghierarchy.models import Organization, OrganizationClass
from django_orghierarchy.utils import get_data_source_model
from .test_importers import mock_request_get


class TestRestImportCommand(TestCase):

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_rest_import_success(self):
        url = 'http://fake.url/organizations/?page=1'
        call_command('import_organizations', url)

        data_source_model = get_data_source_model()
        self.assertEqual(Organization.objects.count(), 3)
        self.assertEqual(data_source_model.objects.count(), 2)
        self.assertEqual(OrganizationClass.objects.count(), 2)

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_rest_import_handle_data_import_error(self):
        url = 'http://not-exist.url/organizatoins/?page=1'
        try:
            call_command('import_organizations', url)
        except DataImportError:
            self.fail('The command does not handle DataImportError')

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_rest_import_with_renamed_source(self):
        url = 'http://fake.url/organizations/?page=1'
        rename_data_source = ['test-source-1: new-source-1', 'test-source-2: new-source-2']
        call_command('import_organizations', url, rename_data_source=rename_data_source)

        data_source_model = get_data_source_model()
        qs = data_source_model.objects.filter(id__in=['new-source-1', 'new-source-2'])
        self.assertTrue(qs.count(), 2)
        self.assertFalse(data_source_model.objects.filter(id__in=['test-source-1', 'test-source-2']).exists())

    def test_rest_import_with_invalid_renamed_source(self):
        url = 'http://fake.url/organizations/?page=1'
        rename_data_source = ['test-source-1: new-source-1', 'test-source-2, new-source-2']
        self.assertRaises(
            CommandError,
            call_command,
            'import_organizations',
            url,
            rename_data_source=rename_data_source,
        )
