from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.routers import DefaultRouter

from django_orghierarchy.api import OrganizationViewSet

router = DefaultRouter()
router.register(r'organization', OrganizationViewSet, 'organization')

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r'^api/', include((router.urls, 'api'), namespace='api')),
]
