from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from django_orghierarchy.admin import OrganizationAdmin
from django_orghierarchy.models import DataSource, Organization
from .factories import OrganizationClassFactory, OrganizationFactory
from .utils import make_admin


class TestDataSourceAdmin(TestCase):

    def test_data_source_admin_is_registered(self):
        is_registered = admin.site.is_registered(DataSource)
        self.assertTrue(is_registered)


class TestOrganizationAdmin(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.organization = OrganizationFactory()

    def test_save_model(self):
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        organization_class = OrganizationClassFactory()
        organization = OrganizationFactory.build(classification=organization_class)
        oa.save_model(request, organization, None, None)
        self.assertEqual(organization.created_by, self.admin)
        self.assertEqual(organization.last_modified_by, self.admin)

        another_admin = make_admin(username='another_admin')
        request.user = another_admin
        oa.save_model(request, organization, None, None)
        self.assertEqual(organization.created_by, self.admin)
        self.assertEqual(organization.last_modified_by, another_admin)
