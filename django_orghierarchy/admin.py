from django.contrib import admin

from .forms import OrganizationForm
from .models import OrganizationClass, Organization
from .utils import get_data_source_model


@admin.register(get_data_source_model())
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(OrganizationClass)
class OrganizationClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'classification', 'name')
    form = OrganizationForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('data_source', 'classification')
