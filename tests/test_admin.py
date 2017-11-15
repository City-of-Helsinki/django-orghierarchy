from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from django_orghierarchy.admin import OrganizationAdmin
from django_orghierarchy.models import Organization
from .factories import OrganizationFactory
from .utils import make_admin


class TestOrganizationAdmin(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.organization = OrganizationFactory()

    def test_get_queryset(self):
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        organization = oa.get_queryset(request).first()
        self.assertNumQueries(0, getattr, organization, 'data_source')
        self.assertNumQueries(0, getattr, organization, 'classification')
