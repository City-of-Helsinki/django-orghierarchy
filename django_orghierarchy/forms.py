from django import forms

from .models import Organization


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'data_source', 'origin_id', 'classification',
            'name', 'founding_date', 'dissolution_date',
            'parent', 'responsible_organization', 'admin_users',
            'regular_users', 'replaced_by',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # An organization cannot be replaced by an organization that have already been replaced
        self.fields['replaced_by'].queryset = Organization.objects.filter(replaced_by__isnull=True)

        # prevent self recursive references
        if self.instance.id:
            self.fields['parent'].queryset = Organization.objects.exclude(id=self.instance.id)
            self.fields['responsible_organization'].queryset = Organization.objects.exclude(id=self.instance.id)
            self.fields['replaced_by'].queryset = self.fields['replaced_by'].queryset.exclude(id=self.instance.id)
