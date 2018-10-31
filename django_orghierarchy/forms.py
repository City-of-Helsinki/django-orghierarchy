from django import forms
from django.forms import widgets
from django.utils.translation import ugettext as _

from .models import Organization
from .utils import get_data_source_model


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'data_source', 'origin_id', 'classification',
            'name', 'founding_date', 'dissolution_date',
            'internal_type', 'parent', 'admin_users',
            'regular_users', 'replaced_by',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the fields can be dynamically exclude, for example set them to readonly in admin
        if 'replaced_by' in self.fields:
            # An organization cannot be replaced by an organization that have already been replaced
            qs = Organization.objects.filter(replaced_by__isnull=True)
            if self.instance.id:
                # prevent self reference
                qs = qs.exclude(id=self.instance.id)
            self.fields['replaced_by'].queryset = qs

        if 'data_source' in self.fields:
            # Only allow selecting data source within editable sources
            self.fields['data_source'].queryset = get_data_source_model().objects.filter(user_editable=True)

        if 'parent' in self.fields and self.instance.id:
            # prevent recursive reference
            desc_ids = self.instance.get_descendants(include_self=True).values_list('id', flat=True)
            self.fields['parent'].queryset = Organization.objects.exclude(id__in=desc_ids)

    def clean(self):
        cleaned_data = super().clean()
        internal_type = cleaned_data.get('internal_type')
        parent = cleaned_data.get('parent')

        if internal_type == Organization.AFFILIATED and parent is None:
            raise forms.ValidationError(_('Affiliated organization must have a parent organization'))

        return cleaned_data


class SubOrganizationForm(forms.ModelForm):
    default_internal_type = Organization.NORMAL

    class Meta:
        model = Organization
        fields = (
            'name', 'founding_date', 'classification', 'data_source', 'origin_id', 'internal_type'
        )
        widgets = {
            'internal_type': widgets.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        kwargs['initial']['internal_type'] = self.default_internal_type
        super().__init__(*args, **kwargs)

        # the fields can be dynamically exclude, for example set them to readonly in admin
        if 'data_source' in self.fields:
            # Only allow selecting data source within editable sources
            self.fields['data_source'].queryset = get_data_source_model().objects.filter(user_editable=True)

    def clean_internal_type(self):
        return self.initial['internal_type']  # do not allow changing internal_type


class AffiliatedOrganizationForm(SubOrganizationForm):
    default_internal_type = Organization.AFFILIATED
