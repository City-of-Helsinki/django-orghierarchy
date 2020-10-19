import swapper
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import DraggableMPTTAdmin
from functools import reduce

from .forms import AffiliatedOrganizationForm, OrganizationForm, SubOrganizationForm
from .models import OrganizationClass, Organization
from .utils import get_data_source_model

data_source_model = swapper.get_model_name('django_orghierarchy', 'DataSource')
# Only register admin when using default data source model
# When the data source model is swapped, client code should
# be responsible for creating admin page for the model
if data_source_model == 'django_orghierarchy.DataSource':
    @admin.register(get_data_source_model())
    class DataSourceAdmin(admin.ModelAdmin):
        list_display = ('id', 'name', 'user_editable')


@admin.register(OrganizationClass)
class OrganizationClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class SubOrganizationInline(admin.TabularInline):
    model = Organization
    verbose_name = _('added sub organization')
    verbose_name_plural = _('added sub organizations')
    fk_name = 'parent'
    form = SubOrganizationForm
    organization_type = Organization.NORMAL
    # these have to be specified separately to prevent seeing redundant internal_type field
    fields = ('name', 'founding_date', 'classification', 'data_source', 'origin_id')
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(internal_type=self.organization_type, data_source__user_editable=True)

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ('data_source', 'origin_id', 'id')


class AddSubOrganizationInline(admin.TabularInline):
    model = Organization
    verbose_name = _('add sub organization')
    verbose_name_plural = _('add sub organizations')
    fk_name = 'parent'
    form = SubOrganizationForm
    organization_type = Organization.NORMAL
    # these have to be specified separately to prevent seeing redundant internal_type field
    fields = ('name', 'founding_date', 'classification', 'data_source', 'origin_id')
    extra = 1

    def get_queryset(self, request):
        return super().get_queryset(request).none()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # we have to have this separate since obj is the parent org, not the new empty one
        # so new suborganizations to be added allow all fields to be defined
        return ('id',)


class ProtectedSubOrganizationInline(admin.TabularInline):
    model = Organization
    verbose_name = _('non-editable sub organization')
    verbose_name_plural = _('non-editable sub organizations')
    fk_name = 'parent'
    form = SubOrganizationForm
    organization_type = Organization.NORMAL
    # these have to be specified separately to prevent seeing redundant internal_type field
    fields = ('name', 'founding_date', 'classification', 'data_source', 'origin_id')
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        return self.form.base_fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(internal_type=self.organization_type, data_source__user_editable=False)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # here obj refers to the *parent* organization, change permission to parent is needed
        if request.user.has_perm('django_orghierarchy.change__organization'):
            return True
        return super().has_change_permission(request, obj)


class AffiliatedOrganizationInline(SubOrganizationInline):
    verbose_name = _('added affiliated organization')
    verbose_name_plural = _('added affiliated organizations')
    form = AffiliatedOrganizationForm
    organization_type = Organization.AFFILIATED

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if (request.user.has_perm('django_orghierarchy.change__organization')
                or request.user.has_perm('django_orghierarchy.change_affiliated_organization')):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # has_change_permission must be True to allow listing, even in read only
        if (request.user.has_perm('django_orghierarchy.delete__organization')
                or request.user.has_perm('django_orghierarchy.delete_affiliated_organization')):
            return True
        return super().has_delete_permission(request, obj)


class AddAffiliatedOrganizationInline(AddSubOrganizationInline):
    verbose_name = _('add affiliated organization')
    verbose_name_plural = _('add affiliated organizations')
    form = AffiliatedOrganizationForm
    organization_type = Organization.AFFILIATED

    def __init__(self, *args, **kwargs):
        # this is the only admin that needs the (hidden) internal_type field, to create a new affiliated organization
        super().__init__(*args, **kwargs)
        self.fields += ('internal_type',)

    def has_add_permission(self, request, obj=None):
        if (request.user.has_perm('django_orghierarchy.add__organization')
                or request.user.has_perm('django_orghierarchy.add_affiliated_organization')):
            return True
        return super().has_add_permission(request, obj)


class ProtectedAffiliatedOrganizationInline(ProtectedSubOrganizationInline):
    verbose_name = _('non-editable affiliated organization')
    verbose_name_plural = _('non-editable affiliated organizations')
    form = AffiliatedOrganizationForm
    organization_type = Organization.AFFILIATED
    extra = 0

    def has_change_permission(self, request, obj=None):
        # here obj refers to the *parent* organization, change permission to parent is needed
        if (request.user.has_perm('django_orghierarchy.change__organization')
                or request.user.has_perm('django_orghierarchy.change_affiliated_organization')):
            return True
        return super().has_change_permission(request, obj)


@admin.register(Organization)
class OrganizationAdmin(DraggableMPTTAdmin):
    filter_horizontal = ('admin_users', 'regular_users')
    form = OrganizationForm
    inlines = [ProtectedSubOrganizationInline, SubOrganizationInline, AddSubOrganizationInline,
               ProtectedAffiliatedOrganizationInline, AffiliatedOrganizationInline, AddAffiliatedOrganizationInline]
    search_fields = ('name', )

    # these fields may not be changed at all in existing organizations
    existing_readonly_fields = ('id', 'data_source', 'origin_id', 'internal_type')
    # these fields may not be changed at all in protected organizations
    protected_readonly_fields = existing_readonly_fields + ('origin_id', 'classification', 'name', 'founding_date',
                                                            'dissolution_date', 'parent',)

    def get_queryset(self, request):
        if not request.user.is_superuser:
            if not request.user.admin_organizations.all():
                return []
            # regular admins have rights to all organizations below their level
            admin_orgs = []
            for admin_org in request.user.admin_organizations.all():
                admin_orgs.append(admin_org.get_descendants(include_self=True))
            # for multiple admin_orgs, we have to combine the querysets and filter distinct
            return reduce(lambda a, b: a | b, admin_orgs).distinct()
        return super().get_queryset(request)

    def get_readonly_fields(self, request, obj=None):
        has_write_access = False
        # queryset is already filtered, but write permissions have to be checked based on organization_type
        if obj and obj.internal_type == Organization.AFFILIATED:
            # full rights also cover affiliated organizations
            has_write_access = (
                request.user.has_perm('django_orghierarchy.change_organization')
                or request.user.has_perm('django_orghierarchy.change_affiliated_organization')
            )
        else:
            has_write_access = request.user.has_perm('django_orghierarchy.change_organization')
        if obj and not has_write_access:
            # has_change_permission has been evaluated to True (i.e. user can
            # open change form in admin) if user has change permissions on
            # affiliated organizations, this i  s to make sure user cannot edit
            # current organization if he does not have change permission on
            # organization
            readonly_fields = self.form.base_fields.copy()
            if request.user.has_perm('django_orghierarchy.change_organization_regular_users'):
                del readonly_fields['regular_users']
            return readonly_fields
        if obj and not obj.data_source.user_editable:
            # Organization data from protected data sources may not be edited
            if not request.user.has_perm('django_orghierarchy.replace_organization'):
                # Replacing an organization in the hierarchy requires extra privileges
                return self.protected_readonly_fields + ('replaced_by',)
            # Protected organizations allow only user fields to be changed
            return self.protected_readonly_fields
        # Editable organizations have no such restrictions, but replacement still requires extra privileges
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields += self.existing_readonly_fields
        if not request.user.has_perm('django_orghierarchy.replace_organization'):
            return readonly_fields + ('replaced_by', )
        return readonly_fields

    def save_model(self, request, obj, form, change):
        # TODO: only allow creating objects for editable data sources?! or only system data source?
        if not obj.pk:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        obj.save()

    def indented_title(self, item):
        """
        Override base method to add custom styles for affiliated organizations
        """
        additional_styles = ''
        if item.internal_type == Organization.AFFILIATED:
            additional_styles = 'color: red;'

        return format_html(
            '<div style="text-indent:{}px; {}">{}</div>',
            item._mpttfield('level') * self.mptt_level_indent,
            additional_styles,
            item,
        )

    def has_change_permission(self, request, obj=None):
        if (request.user.has_perm('django_orghierarchy.change_affiliated_organization')
                or request.user.has_perm('django_orghierarchy.change_organization_regular_users')):
            # allow changing affiliated organization means user can also
            # changing current organization (open change form)
            return True
        return super().has_change_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)

        if (not request.user.has_perm('django_orghierarchy.delete_organization')
                and 'delete_selected' in actions):
            del actions['delete_selected']
        return actions
