import swapper
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractDataSource(models.Model):
    """Abstract data source model.

    Abstract data source model that provides required fields
    for custom data source model.
    """
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class DataSource(AbstractDataSource):
    """Default data source model.

    The default data source model will be used if the project
    does not provide a custom data source model.
    """

    class Meta:
        swappable = swapper.swappable_setting('django_orghierarchy', 'DataSource')


class OrganizationClass(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Organization(models.Model):
    data_source = models.ForeignKey(swapper.get_model_name('django_orghierarchy', 'DataSource'), blank=True, null=True)
    origin_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    classification = models.ForeignKey(OrganizationClass, on_delete=models.PROTECT,
                                       help_text=_('An organization category, e.g. committee'))
    name = models.CharField(max_length=255, help_text=_('A primary name, e.g. a legally recognized name'))
    founding_date = models.DateField(blank=True, null=True, help_text=_('A date of founding'))
    dissolution_date = models.DateField(blank=True, null=True, help_text=_('A date of dissolution'))
    parent = models.ForeignKey('self', null=True, blank=True,
                               help_text=_('The organizations that contain this organization'))
    responsible_organization = models.ForeignKey('self', null=True, blank=True, related_name='affiliated_organization',
                                                 help_text=_('Responsible organization'))

    created_at = models.DateTimeField(auto_now_add=True, help_text=_('The time at which the resource was created'))
    modified_at = models.DateTimeField(auto_now=True, help_text=_('The time at which the resource was updated'))

    class Meta:
        unique_together = ('data_source', 'origin_id')

    def __str__(self):
        if self.parent:
            return '{0} / {1}'.format(self.parent, self.name)
        else:
            return self.name
