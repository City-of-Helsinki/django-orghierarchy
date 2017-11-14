from django.db import models

from django_orghierarchy.models import AbstractDataSource


class CustomDataSource(AbstractDataSource):
    extra_field = models.CharField(max_length=200)


class CustomPrimaryKeyDataSource(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
