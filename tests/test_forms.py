from django.test import TestCase

from django_orghierarchy.forms import OrganizationForm
from django_orghierarchy.models import Organization
from .factories import OrganizationFactory


class TestOrganizationForm(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory()

    def test_init_without_instance(self):
        form = OrganizationForm()
        self.assertQuerysetEqual(form.fields['parent'].queryset, [repr(self.organization)])

    def test_init_with_instance(self):
        form = OrganizationForm(instance=self.organization)
        self.assertQuerysetEqual(form.fields['parent'].queryset, [])

    def test_replaced_by_field_queryset_exclude_already_replaced(self):
        OrganizationFactory(replaced_by=self.organization)
        organization_2 = OrganizationFactory()

        form = OrganizationForm()
        queryset = form.fields['replaced_by'].queryset
        self.assertQuerysetEqual(queryset, [repr(self.organization), repr(organization_2)], ordered=False)

        form = OrganizationForm(instance=organization_2)
        queryset = form.fields['replaced_by'].queryset
        self.assertQuerysetEqual(queryset, [repr(self.organization)])

    def test_clean(self):
        form_data = {
            'data_source': self.organization.data_source_id,
            'origin_id': 'abc',
            'classification': self.organization.classification_id,
            'name': 'test org',
            'internal_type': Organization.AFFILIATED,
            'parent': '',
        }
        form = OrganizationForm(form_data)
        self.assertFalse(form.is_valid())

        form_data['parent'] = self.organization.id
        form = OrganizationForm(form_data)
        self.assertTrue(form.is_valid())
