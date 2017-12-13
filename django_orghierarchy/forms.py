from django import forms
from django.utils.translation import ugettext as _

from .models import Organization


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

        # An organization cannot be replaced by an organization that have already been replaced
        self.fields['replaced_by'].queryset = Organization.objects.filter(replaced_by__isnull=True)

        # prevent self recursive references
        if self.instance.id:
            self.fields['parent'].queryset = Organization.objects.exclude(id=self.instance.id)
            self.fields['replaced_by'].queryset = self.fields['replaced_by'].queryset.exclude(id=self.instance.id)

    def clean(self):
        cleaned_data = super().clean()
        internal_type = cleaned_data['internal_type']
        parent = cleaned_data['parent']

        if internal_type == Organization.AFFILIATED and parent is None:
            raise forms.ValidationError(_('Affiliated organization must have a parent organization'))

        return cleaned_data
