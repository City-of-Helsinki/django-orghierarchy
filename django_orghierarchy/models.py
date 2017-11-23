import swapper
from django.conf import settings
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class AbstractDataSource(models.Model):
    """Abstract data source model.

    Abstract data source model that provides required fields
    for custom data source model.
    """
    id = models.CharField(max_length=100, primary_key=True)
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
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = _('Organization class')
        verbose_name_plural = _('Organization classes')

    def __str__(self):
        return self.name


class Organization(MPTTModel):
    id = models.CharField(max_length=255, primary_key=True, editable=False)
    data_source = models.ForeignKey(swapper.get_model_name('django_orghierarchy', 'DataSource'), blank=True, null=True)
    origin_id = models.CharField(max_length=255, unique=True)

    classification = models.ForeignKey(OrganizationClass, on_delete=models.PROTECT,
                                       help_text=_('An organization category, e.g. committee'))
    name = models.CharField(max_length=255, help_text=_('A primary name, e.g. a legally recognized name'))
    founding_date = models.DateField(blank=True, null=True, help_text=_('A date of founding'))
    dissolution_date = models.DateField(blank=True, null=True, help_text=_('A date of dissolution'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            help_text=_('The organizations that contain this organization'))
    responsible_organization = models.ForeignKey('self', null=True, blank=True, related_name='affiliated_organization',
                                                 help_text=_('Responsible organization'))

    created_at = models.DateTimeField(auto_now_add=True, help_text=_('The time at which the resource was created'))
    modified_at = models.DateTimeField(auto_now=True, help_text=_('The time at which the resource was updated'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_organizations',
                                   null=True, blank=True, editable=False)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='modified_organizations',
                                    null=True, blank=True, editable=False)

    class Meta:
        unique_together = ('data_source', 'origin_id')

    def __str__(self):
        org_hierarchy = self.get_ancestors(include_self=True).values_list('name', flat=True)
        return ' / '.join(org_hierarchy)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.id:
            # the id is only set when creating object, it cannot be changed later
            self.id = '{0}:{1}'.format(self.data_source_id, self.origin_id)
        super().save(*args, **kwargs)
