from django.test import TestCase

from django_orghierarchy.forms import OrganizationForm
from .factories import OrganizationFactory


class TestOrganizationForm(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory()

    def test_init_without_instance(self):
        form = OrganizationForm()
        self.assertQuerysetEqual(form.fields['parent'].queryset, [repr(self.organization)])
        self.assertQuerysetEqual(form.fields['responsible_organization'].queryset, [repr(self.organization)])

    def test_init_with_instance(self):
        form = OrganizationForm(instance=self.organization)
        self.assertQuerysetEqual(form.fields['parent'].queryset, [])
        self.assertQuerysetEqual(form.fields['responsible_organization'].queryset, [])
