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
        list_display = ('id', 'name')


@admin.register(OrganizationClass)
class OrganizationClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class ProtectedOrganizationMixin(object):
    form = None
    organization_type = None

    # these fields may not be changed at all in protected organizations
    protected_readonly_fields = (
        'data_source', 'origin_id', 'classification',
        'name', 'founding_date', 'dissolution_date',
        'internal_type', 'parent',
       )

    def get_readonly_fields(self, request, obj=None):
        has_write_access = False
        # queryset is already filtered, but write permissions have to be checked based on organization_type
        if self.organization_type == Organization.AFFILIATED or (obj and obj.internal_type == Organization.AFFILIATED):
            # full rights also cover affiliated organizations
            has_write_access = request.user.has_perm('django_orghierarchy.change_organization') or request.user.has_perm('django_orghierarchy.change_affiliated_organization')
        else:
            has_write_access = request.user.has_perm('django_orghierarchy.change_organization')
        if obj and not has_write_access:
            # has_change_permission has been evaluated to True (i.e. user can
            # open change form in admin) if user has change permissions on
            # affiliated organizations, this i  s to make sure user cannot edit
            # current organization if he does not have change permission on
            # organization
            return self.form.base_fields
        if obj and not obj.data_source.user_editable:
            # Organization data from protected data sources may not be edited
            if not request.user.has_perm('django_orghierarchy.replace_organization'):
                # Replacing an organization in the hierarchy requires extra privileges
                return self.protected_readonly_fields + ('replaced_by',)
            # Protected organizations allow only user fields to be changed
            return self.protected_readonly_fields
        # Editable organizations have no such restrictions, but replacement still requires extra privileges
        if not request.user.has_perm('django_orghierarchy.replace_organization'):
            return super().get_readonly_fields(request, obj) + ('replaced_by', )
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        # limit the queries if the admin is meant for a specific organization type
        queryset = super().get_queryset(request)
        if self.organization_type:
            return queryset.filter(internal_type=self.organization_type)
        return queryset


class SubOrganizationInline(ProtectedOrganizationMixin, admin.TabularInline):
    model = Organization
    verbose_name = _('sub organization')
    verbose_name_plural = _('sub organizations')
    fk_name = 'parent'
    form = SubOrganizationForm
    organization_type = Organization.NORMAL
    extra = 1


class AffiliatedOrganizationInline(ProtectedOrganizationMixin, admin.TabularInline):
    model = Organization
    verbose_name = _('affiliated organization')
    verbose_name_plural = _('affiliated organizations')
    fk_name = 'parent'
    form = AffiliatedOrganizationForm
    organization_type = Organization.AFFILIATED
    extra = 1

    def has_add_permission(self, request):
        if request.user.has_perm('django_orghierarchy.add_affiliated_organization'):
            return True
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm('django_orghierarchy.change_affiliated_organization'):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.has_perm('django_orghierarchy.delete_affiliated_organization'):
            return True
        return super().has_delete_permission(request, obj)


@admin.register(Organization)
class OrganizationAdmin(ProtectedOrganizationMixin, DraggableMPTTAdmin):
    filter_horizontal = ('admin_users', 'regular_users')
    form = OrganizationForm
    inlines = [SubOrganizationInline, AffiliatedOrganizationInline]

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

    def save_model(self, request, obj, form, change):
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
        if request.user.has_perm('django_orghierarchy.change_affiliated_organization'):
            # allow changing affiliated organization means user can also
            # changing current organization (open change form)
            return True
        return super().has_change_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not request.user.has_perm('django_orghierarchy.delete_organization'):
            del actions['delete_selected']
        return actions
