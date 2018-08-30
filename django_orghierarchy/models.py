import swapper
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class AbstractDataSource(models.Model):
    """Abstract data source model.

    Abstract data source model that provides required fields
    for custom data source model.
    """
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    user_editable = models.BooleanField(default=False, verbose_name=_('Objects may be edited by users'))

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


class DataModel(models.Model):
    id = models.CharField(max_length=255, primary_key=True, editable=False)
    data_source = models.ForeignKey(swapper.get_model_name('django_orghierarchy', 'DataSource'), blank=True, null=True)
    origin_id = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(default=timezone.now, help_text=_('The time at which the resource was created'))
    last_modified_time = models.DateTimeField(auto_now=True, help_text=_('The time at which the resource was updated'))

    class Meta:
        abstract = True
        unique_together = ('data_source', 'origin_id')

    def save(self, *args, **kwargs):
        if not self.id:
            # the id is only set when creating object, it cannot be changed later
            self.id = '{0}:{1}'.format(self.data_source_id, self.origin_id)
        super().save(*args, **kwargs)


class OrganizationClass(DataModel):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('data_source', 'origin_id')
        verbose_name = _('Organization class')
        verbose_name_plural = _('Organization classes')

    def __str__(self):
        return self.name


class Organization(MPTTModel, DataModel):
    NORMAL = 'normal'
    AFFILIATED = 'affiliated'

    INTERNAL_TYPES = (
        (NORMAL, _('Normal organization')),
        (AFFILIATED, _('Affiliated organization')),
    )

    internal_type = models.CharField(max_length=20, choices=INTERNAL_TYPES, default=NORMAL)

    classification = models.ForeignKey(OrganizationClass, on_delete=models.PROTECT, blank=True, null=True,
                                       help_text=_('An organization category, e.g. committee'))
    name = models.CharField(max_length=255, help_text=_('A primary name, e.g. a legally recognized name'))
    founding_date = models.DateField(blank=True, null=True, help_text=_('A date of founding'))
    dissolution_date = models.DateField(blank=True, null=True, help_text=_('A date of dissolution'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            help_text=_('The organizations that contain this organization'))
    admin_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='admin_organizations')
    regular_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                           related_name='organization_memberships')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_organizations',
                                   null=True, blank=True, editable=False)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='modified_organizations',
                                         null=True, blank=True, editable=False)
    replaced_by = models.OneToOneField('self', null=True, blank=True, related_name='replaced_organization',
                                       help_text=_('The organization that replaces this organization'))

    class Meta:
        unique_together = ('data_source', 'origin_id')
        permissions = (
            ('add_affiliated_organization', 'Can add affiliated organization'),
            ('change_affiliated_organization', 'Can change affiliated organization'),
            ('delete_affiliated_organization', 'Can delete affiliated organization'),
            ('replace_organization', 'Can replace an organization with a new one'),
        )

    def __str__(self):
        if self.dissolution_date:
            return self.name + ' (dissolved)'
        return self.name

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # before moving again, the instance must be refreshed from db as it has been moved!
        # https://github.com/django-mptt/django-mptt/issues/257 and
        # https://github.com/django-mptt/django-mptt/issues/279
        new_self = self.__class__.objects.get(pk=self.pk)
        if new_self.parent:
            # move affiliated organization as the first child of parent
            # organization as they need appear before normal child
            # organization when shown in list. We also need to account
            # for the case that an affiliated organization can be changed
            # to a normal organization, thus move normal organization to
            # the last child of parent organization.
            move_positions = {
                self.AFFILIATED: 'first-child',
                self.NORMAL: 'last-child',
            }
            # we must not call move with original self, its fields were outdated by save
            new_self.move_to(new_self.parent, move_positions[self.internal_type])

    @property
    def sub_organizations(self):
        return self.children.filter(internal_type=self.NORMAL)

    @property
    def affiliated_organizations(self):
        return self.children.filter(internal_type=self.AFFILIATED)
