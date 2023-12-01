from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter

from django_orghierarchy.api import OrganizationViewSet

router = DefaultRouter()
router.register(r"organization", OrganizationViewSet, "organization")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((router.urls, "api"), namespace="api")),
]
