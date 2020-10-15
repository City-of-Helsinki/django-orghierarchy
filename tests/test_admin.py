from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory

from django_orghierarchy.admin import OrganizationAdmin, SubOrganizationInline, AddSubOrganizationInline,\
    ProtectedSubOrganizationInline, AffiliatedOrganizationInline, AddAffiliatedOrganizationInline,\
    ProtectedAffiliatedOrganizationInline
from django_orghierarchy.models import DataSource, Organization
from .factories import OrganizationClassFactory, OrganizationFactory, DataSourceFactory
from .utils import clear_user_perm_cache, make_admin


class TestDataSourceAdmin(TestCase):

    def test_data_source_admin_is_registered(self):
        is_registered = admin.site.is_registered(DataSource)
        self.assertTrue(is_registered)


class TestSubOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.normal_admin = make_admin(username='normal_admin', is_superuser=False)

        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)
        self.editable_org = OrganizationFactory(data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = sub_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.editable_org)])

    def test_has_add_permission(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='add_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

    def test_has_change_permission(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='change_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_has_delete_permission(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='delete_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertTrue(has_perm)

    def test_readonly_fields(self):
        sub_org_inline = SubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(('data_source', 'origin_id', 'id'), sub_org_inline.get_readonly_fields(request))
        self.assertEquals(('data_source', 'origin_id', 'id'),
                          sub_org_inline.get_readonly_fields(request, obj=self.editable_org))


class TestAddSubOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.normal_admin = make_admin(username='normal_admin', is_superuser=False)

        self.site = AdminSite()
        self.factory = RequestFactory()

        self.editable_org = OrganizationFactory(data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        sub_org_inline = AddSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = sub_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [])

    def test_has_add_permission(self):
        sub_org_inline = AddSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='add_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertTrue(has_perm)

    def test_has_change_permission(self):
        sub_org_inline = AddSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='change_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

    def test_has_delete_permission(self):
        sub_org_inline = AddSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='delete_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

    def test_readonly_fields(self):
        sub_org_inline = AddSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(('id',), sub_org_inline.get_readonly_fields(request))
        self.assertEquals(('id',),
                          sub_org_inline.get_readonly_fields(request, obj=self.editable_org))


class TestProtectedSubOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)
        self.editable_org = OrganizationFactory(data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        sub_org_inline = ProtectedSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = sub_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.normal_org)])

    def test_has_add_permission(self):
        sub_org_inline = ProtectedSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

    def test_has_change_permission(self):
        sub_org_inline = ProtectedSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = sub_org_inline.has_change_permission(request)
        # permission refers to the *parent* organization, change permission must be given to allow listing
        self.assertTrue(has_perm)

    def test_has_delete_permission(self):
        sub_org_inline = ProtectedSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

    def test_readonly_fields(self):
        sub_org_inline = ProtectedSubOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(sub_org_inline.form.base_fields, sub_org_inline.get_readonly_fields(request))


class TestAffiliatedOrganizationInline(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.normal_admin = make_admin(username='normal_admin', is_superuser=False)

        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)
        self.editable_org = OrganizationFactory(internal_type=Organization.AFFILIATED,
                                                data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = aff_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.editable_org)])

    def test_has_add_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='add_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

    def test_has_change_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='change_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_has_delete_permission(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = aff_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='delete_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = aff_org_inline.has_delete_permission(request)
        self.assertTrue(has_perm)

    def test_readonly_fields(self):
        aff_org_inline = AffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(('data_source', 'origin_id', 'id'), aff_org_inline.get_readonly_fields(request))
        self.assertEquals(('data_source', 'origin_id', 'id'),
                          aff_org_inline.get_readonly_fields(request, obj=self.editable_org))


class TestAddAffiliatedOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.normal_admin = make_admin(username='normal_admin', is_superuser=False)

        self.site = AdminSite()
        self.factory = RequestFactory()

        self.editable_org = OrganizationFactory(data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        sub_org_inline = AddAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = sub_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [])

    def test_has_add_permission(self):
        sub_org_inline = AddAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='add_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_add_permission(request, self.editable_org)
        self.assertTrue(has_perm)

    def test_has_change_permission(self):
        sub_org_inline = AddAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_change_permission(request, self.editable_org)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='change_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_change_permission(request)
        self.assertFalse(has_perm)

    def test_has_delete_permission(self):
        sub_org_inline = AddAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.normal_admin

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(self.normal_admin)
        perm = Permission.objects.get(codename='delete_affiliated_organization')
        self.normal_admin.user_permissions.add(perm)

        has_perm = sub_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

    def test_readonly_fields(self):
        sub_org_inline = AddAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(('id',), sub_org_inline.get_readonly_fields(request))
        self.assertEquals(('id',),
                          sub_org_inline.get_readonly_fields(request, obj=self.editable_org))


class TestProtectedAffiliatedOrganizationInline(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.normal_org = OrganizationFactory(internal_type=Organization.NORMAL)
        self.affiliated_org = OrganizationFactory(internal_type=Organization.AFFILIATED)
        self.editable_org = OrganizationFactory(internal_type=Organization.AFFILIATED,
                                                data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        aff_org_inline = ProtectedAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        qs = aff_org_inline.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.affiliated_org)])

    def test_has_add_permission(self):
        aff_org_inline = ProtectedAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = aff_org_inline.has_add_permission(request, self.editable_org)
        self.assertFalse(has_perm)

    def test_has_change_permission(self):
        aff_org_inline = ProtectedAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = aff_org_inline.has_change_permission(request)
        # permission refers to the *parent* organization, change permission must be given to allow listing
        self.assertTrue(has_perm)

    def test_has_delete_permission(self):
        aff_org_inline = ProtectedAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        has_perm = aff_org_inline.has_delete_permission(request)
        self.assertFalse(has_perm)

    def test_readonly_fields(self):
        aff_org_inline = ProtectedAffiliatedOrganizationInline(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertEquals(aff_org_inline.form.base_fields, aff_org_inline.get_readonly_fields(request))


class TestOrganizationAdmin(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.site = AdminSite()
        self.factory = RequestFactory()

        self.organization = OrganizationFactory()
        self.affiliated_organization = OrganizationFactory(
            internal_type=Organization.AFFILIATED, parent=self.organization)
        self.editable_organization = OrganizationFactory(data_source=(DataSourceFactory(user_editable=True)))

    def test_get_queryset(self):
        org = OrganizationFactory()
        sub_org = OrganizationFactory()
        another_sub_org = OrganizationFactory()
        sub_org.parent = self.organization
        another_sub_org.parent = org
        sub_org.save()
        another_sub_org.save()

        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')

        # test against superuser admin
        request.user = self.admin
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(
            qs,
            [repr(self.organization), repr(self.affiliated_organization), repr(self.editable_organization),
             repr(org), repr(sub_org), repr(another_sub_org)],
            ordered=False)

        # test against non-superuser admin
        request.user = normal_admin
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [])

        self.organization.admin_users.add(normal_admin)
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(qs, [repr(self.organization), repr(self.affiliated_organization), repr(sub_org)])

        org.admin_users.add(normal_admin)
        qs = oa.get_queryset(request)
        self.assertQuerysetEqual(
            qs,
            [repr(self.organization), repr(self.affiliated_organization), repr(org), repr(sub_org),
             repr(another_sub_org)],
            ordered=False)

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

    def test_move_model(self):
        # now, catching this problem requires a four-tier hierarchy and moving next-to-lowest tier
        # back and forth.
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        organization_class = OrganizationClassFactory()
        organization = OrganizationFactory.build(classification=organization_class)
        organization2 = OrganizationFactory.build(classification=organization_class)
        organization3 = OrganizationFactory.build(classification=organization_class)
        organization4 = OrganizationFactory.build(classification=organization_class)
        organization5 = OrganizationFactory.build(classification=organization_class)
        organization6 = OrganizationFactory.build(classification=organization_class)
        organization7 = OrganizationFactory.build(classification=organization_class)
        organization2.parent = organization
        organization3.parent = organization
        organization4.parent = organization2
        organization5.parent = organization2
        organization6.parent = organization3
        organization7.parent = organization4
        oa.save_model(request, organization, None, None)
        oa.save_model(request, organization2, None, None)
        oa.save_model(request, organization3, None, None)
        oa.save_model(request, organization4, None, None)
        oa.save_model(request, organization5, None, None)
        oa.save_model(request, organization6, None, None)
        oa.save_model(request, organization7, None, None)
        self.assertEqual(organization4.parent, organization2)

        organization4.parent = organization3
        oa.save_model(request, organization4, None, None)
        self.assertEqual(organization4.parent, organization3)

        organization4.parent = organization2
        oa.save_model(request, organization4, None, None)
        self.assertEqual(organization4.parent, organization2)

    def test_indented_title(self):
        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = self.admin

        self.assertNotIn('color: red;', oa.indented_title(self.organization))
        self.assertIn('color: red;', oa.indented_title(self.affiliated_organization))

    def test_has_change_permission(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        has_perm = oa.has_change_permission(request)
        self.assertFalse(has_perm)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_affiliated_organization')
        normal_admin.user_permissions.add(perm)

        has_perm = oa.has_change_permission(request)
        self.assertTrue(has_perm)
        normal_admin.user_permissions.remove(perm)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_organization_regular_users')
        normal_admin.user_permissions.add(perm)

        has_perm = oa.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_get_actions(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        actions = oa.get_actions(request)
        self.assertNotIn('delete_selected', actions)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='delete_organization')
        normal_admin.user_permissions.add(perm)

        actions = oa.get_actions(request)
        self.assertIn('delete_selected', actions)

    def test_get_readonly_fields(self):
        normal_admin = make_admin(username='normal_admin', is_superuser=False)

        oa = OrganizationAdmin(Organization, self.site)
        request = self.factory.get('/fake-url/')
        request.user = normal_admin

        form_base_fields = OrganizationAdmin.form.base_fields
        oa_readonly_fields = OrganizationAdmin.readonly_fields
        oa_protected_readonly_fields = OrganizationAdmin.protected_readonly_fields

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields + ('replaced_by',))

        fields = oa.get_readonly_fields(request, self.organization)
        self.assertEqual(fields, form_base_fields)

        fields = oa.get_readonly_fields(request, self.affiliated_organization)
        self.assertEqual(fields, form_base_fields)

        fields = oa.get_readonly_fields(request, self.editable_organization)
        self.assertEqual(fields, form_base_fields)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_organization_regular_users')
        normal_admin.user_permissions.add(perm)

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields + ('replaced_by',))

        fields = oa.get_readonly_fields(request, self.organization)
        fields_minus_regular_users = list(tuple(form_base_fields))
        fields_minus_regular_users.remove('regular_users')
        self.assertEqual(list(tuple(fields)), fields_minus_regular_users)

        fields = oa.get_readonly_fields(request, self.affiliated_organization)
        self.assertEqual(list(tuple(fields)), fields_minus_regular_users)

        fields = oa.get_readonly_fields(request, self.editable_organization)
        self.assertEqual(list(tuple(fields)), fields_minus_regular_users)

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='change_organization')
        normal_admin.user_permissions.add(perm)

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields + ('replaced_by',))

        fields = oa.get_readonly_fields(request, self.organization)
        self.assertEqual(fields, oa_protected_readonly_fields + ('replaced_by',))

        fields = oa.get_readonly_fields(request, self.affiliated_organization)
        self.assertEqual(fields, oa_protected_readonly_fields + ('replaced_by',))

        fields = oa.get_readonly_fields(request, self.editable_organization)
        self.assertEqual(
            fields, oa_readonly_fields + ('id', 'data_source', 'origin_id', 'internal_type', 'replaced_by'))

        clear_user_perm_cache(normal_admin)
        perm = Permission.objects.get(codename='replace_organization')
        normal_admin.user_permissions.add(perm)

        fields = oa.get_readonly_fields(request)
        self.assertEqual(fields, oa_readonly_fields)

        fields = oa.get_readonly_fields(request, self.organization)
        self.assertEqual(fields, oa_protected_readonly_fields)

        fields = oa.get_readonly_fields(request, self.affiliated_organization)
        self.assertEqual(fields, oa_protected_readonly_fields)

        fields = oa.get_readonly_fields(request, self.editable_organization)
        self.assertEqual(fields, oa_readonly_fields + ('id', 'data_source', 'origin_id', 'internal_type'))
