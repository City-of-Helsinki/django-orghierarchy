import swapper
from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class AbstractDataSource(models.Model):
    """Abstract data source model.

    Abstract data source model that provides required fields
    for custom data source model.
    """

    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    user_editable_organizations = models.BooleanField(
        default=False, verbose_name=_("Organizations may be edited by users")
    )

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
        swappable = swapper.swappable_setting("django_orghierarchy", "DataSource")


class DataModel(models.Model):
    id = models.CharField(max_length=255, primary_key=True, editable=False)
    data_source = models.ForeignKey(
        swapper.get_model_name("django_orghierarchy", "DataSource"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    origin_id = models.CharField(max_length=255, blank=True)
    created_time = models.DateTimeField(
        default=timezone.now, help_text=_("The time at which the resource was created")
    )
    last_modified_time = models.DateTimeField(
        auto_now=True, help_text=_("The time at which the resource was updated")
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=("data_source", "origin_id"),
                name="%(app_label)s_%(class)s_data_source_and_origin_id_unique",
            ),
            # PostgreSQL considers null as always unique
            # so origin_id must be unique among null data sources
            UniqueConstraint(
                fields=("origin_id",),
                condition=Q(data_source__isnull=True),
                name="%(app_label)s_%(class)s_origin_id_unique_if_data_source_null",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            # the id is only set when creating object, it cannot be changed later
            self.id = "{0}:{1}".format(self.data_source_id, self.origin_id)
            # Last resort in case unique validations don't catch it:
            # set force_insert to True to avoid accidentally overwriting
            # an existing row
            kwargs["force_insert"] = True
        super().save(*args, **kwargs)


class OrganizationClass(DataModel):
    name = models.CharField(max_length=255)

    class Meta:
        constraints = DataModel.Meta.constraints
        verbose_name = _("Organization class")
        verbose_name_plural = _("Organization classes")

    def __str__(self):
        return self.name


class Organization(MPTTModel, DataModel):
    NORMAL = "normal"
    AFFILIATED = "affiliated"

    INTERNAL_TYPES = (
        (NORMAL, _("Normal organization")),
        (AFFILIATED, _("Affiliated organization")),
    )

    internal_type = models.CharField(
        max_length=20, choices=INTERNAL_TYPES, default=NORMAL
    )

    classification = models.ForeignKey(
        OrganizationClass,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("An organization category, e.g. committee"),
    )
    name = models.CharField(
        max_length=255, help_text=_("A primary name, e.g. a legally recognized name")
    )
    founding_date = models.DateField(
        blank=True, null=True, help_text=_("A date of founding")
    )
    dissolution_date = models.DateField(
        blank=True, null=True, help_text=_("A date of dissolution")
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text=_("The organizations that contain this organization"),
    )
    admin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="admin_organizations"
    )
    regular_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="organization_memberships"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_organizations",
        null=True,
        blank=True,
        editable=False,
    )
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="modified_organizations",
        null=True,
        blank=True,
        editable=False,
    )
    replaced_by = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaced_organization",
        help_text=_("The organization that replaces this organization"),
    )

    @cached_property
    def sub_organizations(self):
        return self.children.filter(internal_type=self.NORMAL)

    @cached_property
    def affiliated_organizations(self):
        return self.children.filter(internal_type=self.AFFILIATED)

    class Meta:
        constraints = DataModel.Meta.constraints
        permissions = (
            ("add_affiliated_organization", "Can add affiliated organization"),
            ("change_affiliated_organization", "Can change affiliated organization"),
            ("delete_affiliated_organization", "Can delete affiliated organization"),
            ("replace_organization", "Can replace an organization with a new one"),
            (
                "change_organization_regular_users",
                "Can add/remove regular users to organizations",
            ),
        )

    def __str__(self):
        if self.dissolution_date:
            return self.name + " (dissolved)"
        return self.name
