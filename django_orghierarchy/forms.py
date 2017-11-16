from django import forms

from .models import Organization


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'data_source', 'origin_id', 'classification',
            'name', 'founding_date', 'dissolution_date',
            'parent', 'responsible_organization',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # prevent self recursive references
        if self.instance.id:
            self.fields['parent'].queryset = Organization.objects.exclude(id=self.instance.id)
            self.fields['responsible_organization'].queryset = Organization.objects.exclude(id=self.instance.id)
