import swapper
from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin

from .forms import OrganizationForm
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


class ChildOrganizationInline(admin.TabularInline):
    model = Organization
    fk_name = 'parent'
    fields = (
        'internal_type', 'data_source', 'origin_id',
        'classification', 'name', 'founding_date',
    )
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(DraggableMPTTAdmin):
    readonly_fields = ('id',)
    filter_horizontal = ('admin_users', 'regular_users')
    form = OrganizationForm
    inlines = [ChildOrganizationInline]

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
