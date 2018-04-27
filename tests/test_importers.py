import re
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from django_orghierarchy.importers import DataImportError, RestAPIImporter
from django_orghierarchy.models import Organization, OrganizationClass
from django_orghierarchy.utils import get_data_source_model

from .factories import OrganizationFactory


class MockResponse:

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError('HTTPError raised')


organization_1 = {
    'id': 111,
    'data_source': 'test-source-1',
    'origin_id': 'ABC-123',
    'classification': 'test-source-1:test-class-1',
    'name': 'Organization-1',
    'founding_date': '2000-01-01',
    'dissolution_date': '2017-01-01',
    'parent': 'http://fake.url/organizations/222/',
    'ignored_field': 'This field will be ignored',
}

organization_2 = {
    'id': 222,
    'data_source': 'test-source-1',
    'origin_id': 'ABC-456',
    'classification': 'test-source-1:test-class-1',
    'name': 'Organization-2',
    'founding_date': '2000-01-01',
    'dissolution_date': None,
    'parent': None,
    'ignored_field': 'This field will be ignored',
}

organization_3 = {
    'id': 333,
    'data_source': 'test-source-2',
    'origin_id': 'XYZ-3',
    'classification': 'test-source-2:test-class-2',
    'name': 'Organizatoin-3',
    'founding_date': '2016-01-01',
    'dissolution_date': None,
    'parent': 'http://fake.url/organizations/111/',
    'ignored_field': 'This field will be ignored',
}

organizations = {
    '111': organization_1,
    '222': organization_2,
    '333': organization_3,
}


def mock_request_get(url):
    m = re.search(r'http://fake.url/organizations/(\d+)/', url)
    if m:
        org_id = m.group(1)
        return MockResponse(organizations[org_id])

    m = re.search(r'http://fake.url/organizations/\?page=(\d+)$', url)
    if m:
        page = m.group(1)
        if page == '1':
            return MockResponse({
                'next': 'http://fake.url/organizations/?page=2',
                'results': [organization_1, organization_2]
            })
        elif page == '2':
            return MockResponse({
                'next': None,
                'results': [organization_3]
            })

    return MockResponse({}, status_code=404)


class TestRestApiImporter(TestCase):

    def setUp(self):
        self.importer = RestAPIImporter('http://fake.url/organizations/?page=1')

    def test_custom_config(self):
        config = {
            'next_key': 'next_page',
            'results_key': 'items',
            'fields': ['classification', 'name', 'parent'],
            'field_config': {
                'classification': {
                    'data_type': 'link',
                }
            }
        }
        importer = RestAPIImporter('http://fake.url/', config)
        self.assertEqual(importer.next_key, 'next_page')
        self.assertEqual(importer.results_key, 'items')

        expected_field_config = {
            'parent': {
                'data_type': 'link',
            },
            'origin_id': {
                'data_type': 'str_lower',
            },
            'classification': {
                'data_type': 'link',
            }
        }
        self.assertDictEqual(importer.field_config, expected_field_config)

    def test_get_organization_class(self):
        data = {'id': 'test-source:test-class'}
        organization_class = self.importer._get_organization_class(data)
        self.assertEqual(organization_class.id, 'test-source:test-class')
        self.assertEqual(OrganizationClass.objects.count(), 1)

        self.importer._get_organization_class(data)
        self.assertEqual(OrganizationClass.objects.count(), 1)  # fetched from cached

    def test_get_data_source(self):
        data = {'id': 'test-source'}
        data_source = self.importer._get_data_source(data)
        self.assertEqual(data_source.id, 'test-source')
        data_source_model = get_data_source_model()
        self.assertEqual(data_source_model.objects.count(), 1)

        self.importer._get_data_source(data)
        self.assertEqual(data_source_model.objects.count(), 1)  # fetched from cached

        self.importer.config['rename_data_source'] = {
            'test-source': 'new-source-name'
        }
        data_source = self.importer._get_data_source(data)
        self.assertEqual(data_source.id, 'new-source-name')
        self.assertEqual(data_source_model.objects.count(), 2)

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_import_data(self):
        self.importer.import_data()
        data_source_model = get_data_source_model()
        self.assertEqual(Organization.objects.count(), 3)
        self.assertEqual(data_source_model.objects.count(), 2)
        self.assertEqual(OrganizationClass.objects.count(), 2)

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_import_organization_with_parent(self):
        organization = self.importer._import_organization(organization_1)
        qs = Organization.objects.all()
        # also created parent organization
        self.assertQuerysetEqual(qs, [repr(organization.parent), repr(organization)], ordered=False)
        self.assertEqual(organization.name, 'Organization-1')
        self.assertNotEqual(organization.id, 111)
        self.assertEqual(organization.parent.name, 'Organization-2')
        self.assertNotEqual(organization.parent_id, 222)

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_import_organization_without_parent(self):
        organization = self.importer._import_organization(organization_2)
        qs = Organization.objects.all()
        self.assertQuerysetEqual(qs, [repr(organization)])
        self.assertEqual(organization.name, 'Organization-2')
        self.assertNotEqual(organization.id, 222)

    def test_import_organization_with_string(self):
        self.assertRaises(DataImportError, self.importer._import_organization, 'test-value')

    def test_import_organization_update_existing(self):
        organization = OrganizationFactory(
            name='existing-organization',
            origin_id=organization_2['origin_id'],
            data_source=self.importer._import_data_source(organization_2['data_source']),
        )
        self.importer._import_organization(organization_2)
        organization.refresh_from_db()

        self.assertQuerysetEqual(Organization.objects.all(), [repr(organization)])
        self.assertEqual(organization.name, 'Organization-2')

    def test_import_data_source_with_string(self):
        data_source = self.importer._import_data_source('test-data-source')
        data_source_model = get_data_source_model()
        qs = data_source_model.objects.all()
        self.assertQuerysetEqual(qs, [repr(data_source)])
        self.assertEqual(data_source.id, 'test-data-source')

    def test_import_data_source_with_dict_data(self):
        data = {
            'id': 'test-data-source'
        }
        data_source = self.importer._import_data_source(data)
        data_source_model = get_data_source_model()
        qs = data_source_model.objects.all()
        self.assertQuerysetEqual(qs, [repr(data_source)])
        self.assertEqual(data_source.id, 'test-data-source')

    def test_import_organization_class_with_string(self):
        organization_class = self.importer._import_organization_class('test-source-1:test-org-class')
        qs = OrganizationClass.objects.all()
        self.assertQuerysetEqual(qs, [repr(organization_class)])
        self.assertEqual(organization_class.id, 'test-source-1:test-org-class')

    def test_import_organization_class_with_simple_string(self):
        organization_class = self.importer._import_organization_class('class-with-no-source')
        qs = OrganizationClass.objects.all()
        self.assertQuerysetEqual(qs, [repr(organization_class)])
        self.assertEqual(organization_class.id, 'OpenDecisionAPI:class-with-no-source')

    def test_import_organization_class_with_dict_data(self):
        data = {
            'id': 999,
            'origin_id': 'test-org-class',
            'name': 'test-org-class',
            'data_source': 'test-source-1',
        }
        organization_class = self.importer._import_organization_class(data)
        qs = OrganizationClass.objects.all()
        self.assertQuerysetEqual(qs, [repr(organization_class)])
        self.assertEqual(organization_class.name, 'test-org-class')
        self.assertEqual(organization_class.id, 'test-source-1:test-org-class')

    def test_import_organization_class_with_simple_dict_data(self):
        data = {
            'id': 999,
            'name': 'test-org-class'
        }
        organization_class = self.importer._import_organization_class(data)
        qs = OrganizationClass.objects.all()
        self.assertQuerysetEqual(qs, [repr(organization_class)])
        self.assertEqual(organization_class.name, 'test-org-class')
        self.assertEqual(organization_class.id, 'OpenDecisionAPI:999')

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_data_iter(self):
        url = 'http://fake.url/organizations/?page=1'
        iterator = self.importer._data_iter(url)
        iter_len = len(list(iterator))
        self.assertEqual(iter_len, 3)

        url = 'http://fake.url/organizations/?page=2'
        iterator = self.importer._data_iter(url)
        iter_len = len(list(iterator))
        self.assertEqual(iter_len, 1)

        url = 'http://not-exist.url/organizations/'
        self.assertRaises(DataImportError, list, self.importer._data_iter(url))

    def test_get_field_value_empty_value(self):
        value = self.importer._get_field_value(organization_2, 'dissolution_date', {})
        self.assertIsNone(value)

    def test_get_field_value_different_source_field(self):
        config = {
            'source_field': 'id',
        }
        value = self.importer._get_field_value(organization_1, 'origin_id', config)
        self.assertEqual(value, 111)

    def test_get_field_value_not_exist_field(self):
        config = {
            'source_field': 'not-exist-field',
        }
        self.assertRaises(
            DataImportError,
            self.importer._get_field_value,
            organization_1,
            'origin_id',
            config,
        )

    def test_get_field_value_not_exist_data_type(self):
        config = {
            'data_type': 'not-exist-data-type',
        }
        self.assertRaises(
            DataImportError,
            self.importer._get_field_value,
            organization_1,
            'origin_id',
            config,
        )

    @patch('requests.get', MagicMock(return_value=MockResponse('test-get-return')))
    def test_get_field_value_link_data_type(self):
        config = {
            'data_type': 'link',
        }
        value = self.importer._get_field_value({'name': 'http://fake.url/'}, 'name', config)
        self.assertEqual(value, 'test-get-return')

    def test_get_field_value_str_lower_data_type(self):
        config = {
            'data_type': 'str_lower',
        }
        value = self.importer._get_field_value(organization_1, 'origin_id', config)
        self.assertEqual(value, 'abc-123')

    def test_get_field_value_regex_data_type(self):
        config = {
            'data_type': 'regex',
        }
        # test raise DataImportError if no pattern is provided
        self.assertRaises(
            DataImportError,
            self.importer._get_field_value,
            organization_1,
            'origin_id',
            config,
        )

        config = {
            'data_type': 'regex',
            'pattern': r'\w+\-(\d+)',
        }
        value = self.importer._get_field_value(organization_1, 'origin_id', config)
        self.assertEqual(value, '123')

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_get_field_value_related_fields(self):
        value = self.importer._get_field_value(organization_1, 'data_source', {})
        self.assertEqual(value.id, 'test-source-1')

        value = self.importer._get_field_value(organization_1, 'classification', {})
        self.assertEqual(value.id, 'test-source-1:test-class-1')

        value = self.importer._get_field_value(organization_1, 'parent', {'data_type': 'link'})
        self.assertEqual(value.name, 'Organization-2')

    def test_get_regex_data(self):
        pattern = r'\w+\-(\d+)'
        self.assertRaises(
            DataImportError,
            self.importer._get_regex_data,
            '123',
            pattern,
        )

        data = self.importer._get_regex_data('abc-123', pattern)
        self.assertEqual(data, '123')

    @patch('requests.get', MagicMock(side_effect=mock_request_get))
    def test_get_link_data(self):
        invalid_url = 'abc.123'
        self.assertRaises(DataImportError, self.importer._get_link_data, invalid_url)

        url = 'http://not-exist.url/organizations/111/'
        self.assertRaises(DataImportError, self.importer._get_link_data, url)

        url = 'http://fake.url/organizations/111/'
        data = self.importer._get_link_data(url)
        self.assertEqual(data, organization_1)
