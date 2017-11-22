from django.test import TestCase

from .factories import DataSourceFactory, OrganizationClassFactory, OrganizationFactory


class TestDataSource(TestCase):

    def setUp(self):
        self.data_source = DataSourceFactory(name='test name')

    def test__str__(self):
        self.assertEqual(self.data_source.__str__(), 'test name')


class TestOrganizationClass(TestCase):

    def setUp(self):
        self.organization_class = OrganizationClassFactory(name='test name')

    def test__str__(self):
        self.assertEqual(self.organization_class.__str__(), 'test name')


class TestOrganization(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory(name='test name')

    def test__str__(self):
        self.assertEqual(self.organization.__str__(), 'test name')

        self.organization.parent = OrganizationFactory(name='parent name')
        self.assertEqual(self.organization.__str__(), 'parent name / test name')

    def test_save(self):
        data_source = DataSourceFactory(id='data-source')
        organization = OrganizationFactory(data_source=data_source, origin_id='ABC123')
        self.assertEqual(organization.id, 'data-source:ABC123')

        organization.origin_id = 'XYZ'
        organization.save()
        self.assertEqual(organization.id, 'data-source:XYZ')
