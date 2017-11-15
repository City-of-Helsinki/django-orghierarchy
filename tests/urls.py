from django.conf.urls import include, url
from django.contrib import admin

from django_orghierarchy.routers import router

urlpatterns = [
    url(r"^admin/", admin.site.urls),
]
