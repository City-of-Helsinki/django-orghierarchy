from django.test import TestCase

from django_orghierarchy.models import Organization
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
        self.parent_organization = OrganizationFactory(name='parent name')
        self.organization = OrganizationFactory(name='test name', parent=self.parent_organization)
        self.affiliated_organization = OrganizationFactory(
            name='test aff org',
            parent=self.parent_organization,
            internal_type=Organization.AFFILIATED,
        )

    def test__str__(self):
        self.assertEqual(self.parent_organization.__str__(), 'parent name')
        self.assertEqual(self.organization.__str__(), 'test name')

    def test_save(self):
        data_source = DataSourceFactory(id='data-source')
        organization = OrganizationFactory(data_source=data_source, origin_id='ABC123')
        self.assertEqual(organization.id, 'data-source:ABC123')

        organization.origin_id = 'XYZ'
        organization.save()
        # test the id is not changed
        self.assertEqual(organization.id, 'data-source:ABC123')

    def test_sub_organizations(self):
        qs = self.parent_organization.sub_organizations
        self.assertQuerysetEqual(qs, [repr(self.organization)])

    def test_affiliated_organizations(self):
        qs = self.parent_organization.affiliated_organizations
        self.assertQuerysetEqual(qs, [repr(self.affiliated_organization)])
