from django.test import TestCase

from django_orghierarchy.forms import OrganizationForm, SubOrganizationForm, AffiliatedOrganizationForm
from django_orghierarchy.models import Organization
from .factories import OrganizationClassFactory, DataSourceFactory, OrganizationFactory


class TestOrganizationForm(TestCase):

    def setUp(self):
        self.organization = OrganizationFactory()
        self.data_source = DataSourceFactory(user_editable=True)

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
            'data_source': self.data_source.id,
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


class TestSubOrganizationForm(TestCase):

    def setUp(self):
        self.data_source = DataSourceFactory(user_editable=True)
        self.organization_class = OrganizationClassFactory()

    def test__init__(self):
        form = SubOrganizationForm()
        self.assertEqual(form.initial['internal_type'], Organization.NORMAL)

        form = SubOrganizationForm(initial={'internal_type': Organization.AFFILIATED})
        self.assertEqual(form.initial['internal_type'], Organization.NORMAL)

    def test_clean_internal_type(self):
        form_data = {
            'internal_type': Organization.NORMAL,
            'data_source': self.data_source.id,
            'origin_id': 'sub-org',
            'classification': self.organization_class.id,
            'name': 'sub organization',
        }
        form = SubOrganizationForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['internal_type'], Organization.NORMAL)

        form_data['internal_type'] = Organization.AFFILIATED
        form = SubOrganizationForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['internal_type'], Organization.NORMAL)


class TestAffiliatedOrganizationForm(TestCase):

    def setUp(self):
        self.data_source = DataSourceFactory(user_editable=True)
        self.organization_class = OrganizationClassFactory()

    def test__init__(self):
        form = AffiliatedOrganizationForm()
        self.assertEqual(form.initial['internal_type'], Organization.AFFILIATED)

        form = AffiliatedOrganizationForm(initial={'internal_type': Organization.NORMAL})
        self.assertEqual(form.initial['internal_type'], Organization.AFFILIATED)

    def test_clean_internal_type(self):
        form_data = {
            'internal_type': Organization.NORMAL,
            'data_source': self.data_source.id,
            'origin_id': 'sub-org',
            'classification': self.organization_class.id,
            'name': 'sub organization',
        }
        form = AffiliatedOrganizationForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['internal_type'], Organization.AFFILIATED)

        form_data['internal_type'] = Organization.AFFILIATED
        form = AffiliatedOrganizationForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['internal_type'], Organization.AFFILIATED)
