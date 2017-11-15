from rest_framework import serializers, viewsets

from .models import Organization, OrganizationClass
from .utils import get_data_source_model


class DataSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_data_source_model()
        fields = '__all__'


class OrganizationClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationClass
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    data_source = DataSourceSerializer()
    classification = OrganizationClassSerializer()

    class Meta:
        model = Organization
        fields = '__all__'


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.select_related('data_source', 'classification')
    serializer_class = OrganizationSerializer
