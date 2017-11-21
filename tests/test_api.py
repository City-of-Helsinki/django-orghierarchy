from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import DataSourceFactory, OrganizationFactory


class OrganizationAPITestCase(APITestCase):

    def setUp(self):
        data_source = DataSourceFactory(name='abc')
        self.organization = OrganizationFactory(data_source=data_source, origin_id='123')

    def test_organization_list(self):
        url = reverse('api:organization-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_organization(self):
        url = reverse('api:organization-detail', kwargs={'pk': self.organization.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_modify_organization(self):
        url = reverse('api:organization-detail', kwargs={'pk': self.organization.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_organization(self):
        url = reverse('api:organization-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
