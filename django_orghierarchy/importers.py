import copy
import logging
import re
import urllib.parse
import warnings
from enum import Enum

import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from .models import Organization, OrganizationClass
from .utils import get_data_source_model

logger = logging.getLogger(__name__)


class DataImportError(Exception):
    pass


class DataType(Enum):
    VALUE = "value"
    STR_LOWER = "str_lower"
    LINK = "link"
    REGEX = "regex"
    ORG_ID = "org_id"
    ORG_ID_REGEX = "org_id_regex"


class RestAPIImporter:
    r"""This class allows importing organization data from a REST API endpoint. The
    default configuration supports the 6aika Open Decision API specification:
    https://github.com/6aika/api-paatos

    The importer will also create data sources and organization classes if does not
    exist. If a single value is provided to `data_source` and `classification` fields,
    then the importer assumes the value is the name of the data source or organization
    class. If an object (dict) is provided to `data_source` and `classification` fields,
    then the importer will create objects with object data. Either full object data or a
    link to full object data should be provided to parent field so that the importer can
    create parent organization before creating child organization.

    For use in multi-source setups, the importer may optionally create a parent
    organization for the data source that is the common parent of all imported top-level
    organizations. This way, separate organization hierarchies from different data
    sources may be stored in the same application.

    The client code can override the default config or pass in a config object to allow
    the importer parsing different REST API structures.

    Config options:
        - next_key: The url to the next page if the source data is paginated, or None if
            not.
        - results_key: The object key to the list of organization objects, or None if
            the list is at root level.
        - fields: The fields of which the values will be imported. The same fields will
            be imported in organization classes, if present.
        - update_fields: The fields to update if the organization with same origin_id
            and data source exists.
        - skip_classifications: List of organization classifications which will cause
            organizations of this type to be skipped upon import.
        - has_meta: Does the JSON contain a separate object for pagination. Default
            False.
        - deprecated: Is the configuration considered deprecated. Default False.
        - field_config: Configs for each field. Config options:
            - source_field: The source data object key where the field value comes from.
                Defaults to original field name.
            - data_type: The data type for the field, can be 'value', 'str_lower',
                'link', 'regex', 'org_id' or 'org_id_regex'.
                Defaults to 'value'. If the data type is 'value', it will return the
                value from source data; if the data type is 'str_lower', it will return
                the value stringified and lowercased; if the data type is 'link', it
                will return the data fetched from the link; if the data type is 'regex',
                it will return the value extracted from the given pattern. If the data
                type is 'org_id' or 'org_id_regex', it will return the organization in
                the JSON with the given 'id'.
            - pattern: The pattern to extract the value from the source data. Only used
                when data_type is 'regex' or 'org_id_regex'.
            - unquote: Should the value be run through urllib.parse.unquote. Defaults to
                 False.
            - unwrap_list: Value is wrapped inside of a list. Return the first value on
                the list. Defaults to False.
            - optional: Whether the importer will continue if the field is missing.
                Defaults to False.
        - rename_data_source: Data sources that are renamed during import.
        - default_data_source: Data source id to use for objects without data source.
        - default_parent_organization: If set, name of the parent organization to be
            created for all imported top level organizations.

    Example config:
        {
            "next_key": "next",
            "results_key": "results",
            "fields": ["origin_id", "data_source", "classification"],
            "update_fields": ["classification"],
            "field_config": {
                "origin_id": {
                    "source_field": "id",
                    "data_type": "regex",
                    "pattern": r"abc:(\d+)",
                },
                "parent": {
                    "data_type": "link",
                },
            },
            "rename_data_source": {
                "original_name_1": "new_name_1",
                "original_name_2": "new_name_2",
            },
            "default_data_source": "new_name_1",
            "default_parent_organization": None,
        }
    """

    # https://api.hel.fi/paatos/v1/organization/
    paatos_config = {
        "deprecated": True,
        "has_meta": False,
        "next_key": "next",
        "results_key": "results",
        "fields": [
            "data_source",
            "origin_id",
            "classification",
            "name",
            "founding_date",
            "dissolution_date",
            "parent",
        ],
        "update_fields": [
            "classification",
            "name",
            "founding_date",
            "dissolution_date",
            "parent",
        ],
        "field_config": {
            "parent": {
                "data_type": "link",
            },
            "origin_id": {
                "data_type": "str_lower",
            },
        },
        "default_data_source": "OpenDecisionAPI",
    }

    # https://dev.hel.fi/apis/openahjo
    # https://dev.hel.fi/paatokset/v1/organization/
    # https://github.com/City-of-Helsinki/openahjo
    openahjo_config = {
        "has_meta": True,
        "next_key": "next",
        "results_key": "objects",
        "fields": [
            "origin_id",
            "classification",
            "name",
            "founding_date",
            "dissolution_date",
            "parent",
        ],
        "skip_classifications": ["office_holder", "team", "subteam", "trustee"],
        "update_fields": [
            "classification",
            "name",
            "founding_date",
            "dissolution_date",
            "parent",
        ],
        "field_config": {
            "name": {
                "source_field": "name_fi",
            },
            "classification": {
                "source_field": "type",
            },
            "parent": {
                "source_field": "parents",
                "data_type": "org_id_regex",
                "unwrap_list": True,
                "unquote": True,
                "pattern": r"\/(\w+:\w+)\/$",
                "optional": True,
            },
            "origin_id": {
                "data_type": "str_lower",
            },
        },
        "default_data_source": "OpenAhjoAPI",
    }

    tprek_config = {
        "has_meta": False,
        "next_key": None,
        "results_key": None,
        "fields": [
            "origin_id",
            "classification",
            "name",
            "parent",
        ],
        "update_fields": [
            "classification",
            "name",
            "parent",
        ],
        "field_config": {
            "parent": {
                "source_field": "parent_id",
                "data_type": "org_id",
                "optional": True,
            },
            "origin_id": {
                "source_field": "id",
                "data_type": "value",
            },
            "classification": {
                "source_field": "organization_type",
                "optional": True,
            },
            "name": {
                "source_field": "name_fi",
                "optional": True,
            },
        },
        "default_data_source": "tprek",
        "default_parent_organization": "Pääkaupunkiseudun toimipisterekisteri",
    }

    default_config = paatos_config
    timeout = 10

    def __init__(self, url, config=None):
        self.url = url

        self.config = copy.deepcopy(self.default_config)
        config = copy.deepcopy(config)
        if config:
            # only consider fields listed in given config when merging field configs
            default_field_config = self.config.pop("field_config")
            given_field_config = config.pop("field_config")
            merged_field_config = {}
            for field in config.get("fields", None):
                if field in given_field_config:
                    merged_field_config[field] = given_field_config[field]
                elif field in default_field_config:
                    merged_field_config[field] = default_field_config[field]
            self.config["field_config"] = merged_field_config
            self.config.update(config)
        logger.info(
            f"Importing organization data from {self.url} with the following config:"
        )
        logger.info(self.config)
        self.related_import_methods = {
            "data_source": self._import_data_source,
            "classification": self._import_organization_class,
            "parent": self._import_organization,
        }

        if self.config.get("deprecated", False):
            warnings.warn(
                "RestAPIImporter is initialized with a deprecated configuration.",
                DeprecationWarning,
                stacklevel=2,
            )

        self._organization_classes = {}
        self._data_sources = {}
        self._organizations = {}
        self._default_parent = None
        if self.config.get("default_parent_organization", None):
            origin_id_config = self.config["field_config"].get("origin_id", None)
            origin_id_field = (
                origin_id_config["source_field"] if origin_id_config else "origin_id"
            )
            data_source_config = self.config["field_config"].get("data_source", None)
            data_source_field = (
                data_source_config["source_field"]
                if data_source_config
                else "data_source"
            )
            name_config = self.config["field_config"].get("name", None)
            name_field = name_config["source_field"] if name_config else "name"
            default_parent_data = {
                origin_id_field: self.config["default_data_source"],
                data_source_field: self.config["default_data_source"],
                name_field: self.config["default_parent_organization"],
            }
            self._default_parent = self._import_organization(default_parent_data)
        # Save all the data from the REST endpoint in a single dict.
        # This is for cases where we need to access the data by id instead of link.
        # Caching is necessary for importing all parent organizations before
        # their children.
        self._data_dict = {}
        for data_item in self._data_iter(self.url):
            self._data_dict[data_item["id"]] = data_item

    @property
    def fields(self):
        return self.config["fields"]

    @property
    def update_fields(self):
        return self.config["update_fields"]

    @property
    def field_config(self):
        return self.config["field_config"]

    @property
    def has_meta(self):
        """Whether the response contains a separate object for pagination."""
        return self.config.get("has_meta", False)

    @property
    def next_key(self):
        """Object key that stores the link to the next page"""
        return self.config["next_key"]

    @property
    def results_key(self):
        """Object key that stores the list of organizations"""
        return self.config["results_key"]

    @property
    def rename_data_source(self):
        """Data source renaming configs"""
        return self.config.get("rename_data_source") or {}

    @property
    def skip_classifications(self):
        """List of organization classifications to skip"""
        return self.config.get("skip_classifications") or []

    @property
    def default_data_source(self):
        """Default data source string"""
        return self.config["default_data_source"]

    def _build_resource_url(self, resource_id) -> str:
        """Build an url for the given resource id.

        Resource identifiers in the data might be missing the scheme+host part.
        With
        - self.url = "https://dev.hel.fi/paatokset/v1/organization/" and
        - resource_id = "/paatokset/v1/organization/?limit=20&offset=20"

        the expected output is:
        "https://dev.hel.fi/paatokset/v1/organization/?limit=20&offset=20"
        """
        return urllib.parse.urljoin(self.url, resource_id)

    def _get_organization_class(self, data):
        """Get organization class for the given object data

        The method will first try to get the organization class from cache, and
        then get from database if not cached.
        """
        # organization class supports id, data_source, origin_id and name.
        supported_fields = {"id", "origin_id", "data_source", "name"}
        identifier = data.get("id")
        # organization class requires data source and origin_id.
        if isinstance(identifier, str) and ":" in identifier:
            if "data_source" not in data:
                data["data_source"] = identifier.split(":")[0]
            if "origin_id" not in data:
                data["origin_id"] = identifier.split(":")[1]
        # provided id used if origin id missing
        if "origin_id" not in data or not data["origin_id"]:
            data["origin_id"] = identifier
        # default data source used if missing
        if "data_source" not in data or not data["data_source"]:
            data["data_source"] = self.default_data_source
        data_source_instance = self.related_import_methods["data_source"](
            data["data_source"]
        )
        # reformat id to fit our model
        if not isinstance(identifier, str) or ":" not in identifier:
            data["id"] = data_source_instance.pk + ":" + str(identifier)
        data["data_source"] = data_source_instance
        # extra fields should not crash the import. Only use specified fields.
        data = {
            field: value for (field, value) in data.items() if field in supported_fields
        }
        if identifier not in self._organization_classes:
            defaults = {"name": data.pop("name", data["id"])}
            organization_class, _ = OrganizationClass.objects.get_or_create(
                **data, defaults=defaults
            )
            self._organization_classes[identifier] = organization_class
        return self._organization_classes[identifier]

    def _get_data_source(self, data):
        """Get data source for the given object data

        The method will first try to get the data source from cache, and
        then get from database if not cached.
        """
        identifier = data["id"]

        if identifier in self.rename_data_source:
            identifier = self.rename_data_source[identifier]
            data["id"] = identifier

        if identifier not in self._data_sources:
            data_source_model = get_data_source_model()
            data_source, _ = data_source_model.objects.get_or_create(**data)
            self._data_sources[identifier] = data_source
        return self._data_sources[identifier]

    def import_data(self):
        """Import data"""
        for data_item in self._data_dict.values():
            self._import_organization(data_item)

    @transaction.atomic
    def _import_organization(self, data):
        """Import single organization.

        The organization import is transactional so, for example, we do not
        accidentally save organization without parent if the parent organization
        saving failed for some reason.
        """
        # id must always be present
        config = self.field_config.get("origin_id") or {}
        if isinstance(data, dict):
            incoming_data = data
        else:
            raise DataImportError("Organization data must be dict.")
        origin_id = self._get_field_value(incoming_data, "origin_id", config)

        if origin_id in self._organizations:
            # No need to re-import/update an organization which is already
            # imported once in this run.
            logger.debug(f"Using cached Organization: {origin_id}")
            return self._organizations[origin_id]

        # data source may be missing altogether, or it may be optional
        data_source = None
        config = self.field_config.get("data_source") or {}
        try:
            data_source = self._get_field_value(incoming_data, "data_source", config)
        except DataImportError:
            if not config or config.get("optional"):
                pass
            else:
                raise
        if not data_source:
            data_source = self._get_field_value(
                {"data_source": self.default_data_source},
                "data_source",
                {"data_type": "value"},
            )

        logger.debug(f"Importing Organization: {origin_id}")

        # id is never imported in default config

        try:
            return self._import_organization_update(
                incoming_data, origin_id, data_source
            )
        except Organization.DoesNotExist:
            return self._import_organization_create(
                incoming_data, origin_id, data_source
            )

    def _import_organization_update(self, incoming_data, origin_id, data_source):
        """Update an existing organization upon import."""
        values_to_update = {}
        for field in self.update_fields:
            config = self.field_config.get(field) or {}
            try:
                value = self._get_field_value(incoming_data, field, config)
            except DataImportError:
                if config.get("optional"):
                    continue
                else:
                    raise
            values_to_update[field] = value

        # Organization parent (and its parent) have been imported and updated
        # recursively. If one of them used to be the descendant of this organization,
        # this might result in mptt InvalidMove exception if this organization instance
        # is not up-to-date with the database.
        # See https://github.com/django-mptt/django-mptt/issues/650

        # Therefore, we may only fetch the organization from the db *after* all its
        # parents have been processed, to get up-to-date status of the mptt tree before
        # saving each organization. Enforce lower case id standard, but recognize upper
        # case ids as equal:
        organization = Organization.objects.get(
            origin_id__iexact=origin_id, data_source=data_source
        )
        logger.info(f"Updating organization: {origin_id}")
        for field, value in values_to_update.items():
            setattr(organization, field, value)
        if (
            self.config.get("default_parent_organization", None)
            and not organization.parent
            and organization != self._default_parent
        ):
            organization.parent = self._default_parent
        organization.save()
        logger.debug(f"Caching Organization: {origin_id}")
        self._organizations[organization.origin_id] = organization

        return organization

    def _import_organization_create(self, incoming_data, origin_id, data_source):
        """Create a new Organization instance upon import."""
        object_data = {"origin_id": origin_id, "data_source": data_source}
        for field in self.fields:
            config = self.field_config.get(field) or {}
            try:
                object_data[field] = self._get_field_value(incoming_data, field, config)
            except DataImportError:
                if config.get("optional"):
                    continue
                else:
                    raise

        # Check if we're supposed to skip importing organizations of this class
        classification = object_data.get("classification")
        if classification and classification.origin_id in self.skip_classifications:
            self._organizations[origin_id] = None
            logger.info(
                f"Skipping organization: {origin_id} with type: {classification}"
            )
            return None

        logger.info(f"Creating Organization: {origin_id}")
        organization = Organization.objects.create(**object_data)
        if (
            self.config.get("default_parent_organization", None)
            and not organization.parent
            and organization != self._default_parent
        ):
            organization.parent = self._default_parent
            organization.save()
        logger.debug(f"Caching Organization: {origin_id}")
        self._organizations[origin_id] = organization

        return organization

    def _import_data_source(self, data):
        """Import data source

        If a single value is provided to data_source field, it assume it's
        the id of the data source.
        """
        if isinstance(data, dict):
            object_data = data
        else:
            object_data = {"id": data}

        return self._get_data_source(object_data)

    def _import_organization_class(self, data):
        """Import organization class.

        If a single value is provided to classification field, it assume it's
        the id of the organization class.

        If a dict is provided, origin_id is used if present, otherwise id.
        """
        if isinstance(data, dict):
            object_data = {k: v for k, v in data.items() if k != "id"}
            object_data["id"] = data["origin_id"] if "origin_id" in data else data["id"]
        else:
            object_data = {"id": data}

        return self._get_organization_class(object_data)

    def _data_iter(self, url):
        """Iterate over data items in the REST API endpoint.

        The iterator will follow over next page links if available.
        """
        logger.info(f"Start reading data from {url} ...")

        r = requests.get(url, timeout=self.timeout)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise DataImportError(e) from e

        data = r.json()
        for data_item in data[self.results_key] if self.results_key else data:
            yield data_item

        logger.info(f"Reading data from {url} completed")

        if self.next_key:
            if self.has_meta:
                next_page_url = data["meta"][self.next_key]
            else:
                next_page_url = data[self.next_key]

            if next_page_url:
                yield from self._data_iter(self._build_resource_url(next_page_url))

    def _get_field_value(self, data_item, field, config):
        """Get source value for the field from the data item

        If source_field is specified in field config, the source_field
        will be used to get the source value, otherwise the model field
        will be used.

        If the data type is DataType.VALUE, the value will be returned;
        If the data type is DataType.STR_LOWER, the value will be returned stringified
        to lower case;
        If the data type is DataType.ORG_ID, corresponding organization will be
        returned;
        If the data type is DataType.LINK, the data in the link will be returned;
        If the data type is DataType.REGEX, the extracted value for the pattern will be
        returned.
        """
        source_field = config.get("source_field") or field
        try:
            value = data_item[source_field]
        except KeyError as e:
            raise DataImportError(
                f"Field not found in source data: {source_field}"
            ) from e

        if config.get("unwrap_list") and not value and isinstance(value, list):
            # Unwrap an empty list to avoid possible errors.
            value = None

        if not value:
            return value

        if config.get("data_type"):
            try:
                data_type = DataType(config["data_type"])
            except ValueError:
                raise DataImportError(
                    f"Invalid data type: {config['data_type']}. "
                    f"Supported data types are: "
                    f"{', '.join([e.value for e in DataType])}"
                )
        else:
            data_type = DataType.VALUE

        if data_type in (DataType.REGEX, DataType.ORG_ID_REGEX) and not config.get(
            "pattern"
        ):
            raise DataImportError(f"No regex pattern provided for the field: {field}")

        if config.get("unwrap_list"):
            if len(value) > 1:
                warnings.warn(
                    "More than one value in the list, unwrap_list only "
                    "unwraps the first value in the list.",
                    UserWarning,
                    stacklevel=2,
                )
            value = value[0]
        if config.get("unquote"):
            value = urllib.parse.unquote(value)

        if data_type == DataType.STR_LOWER:
            value = str(value).lower()
        elif data_type == DataType.ORG_ID:
            value = self._data_dict.get(value, None)
        elif data_type == DataType.ORG_ID_REGEX:
            value = self._get_regex_data(value, config["pattern"])
            value = self._data_dict.get(value, None)
        elif data_type == DataType.LINK:
            value = self._get_link_data(value)
        elif data_type == DataType.REGEX:
            value = self._get_regex_data(value, config["pattern"])

        # import related objects
        if field in self.related_import_methods:
            import_method = self.related_import_methods[field]
            value = import_method(value)

        return value

    @staticmethod
    def _get_regex_data(value, pattern):
        """Extract value from original string value with the given regex pattern"""
        match = re.search(pattern, value)
        if match:
            data = match.group(1)
        else:
            raise DataImportError(
                f"Cannot extract value from string {value} with pattern {pattern}"
            )
        return data

    def _get_link_data(self, value):
        """Get data fetched from the link"""
        validator = URLValidator()
        try:
            validator(value)
        except ValidationError as e:
            raise DataImportError(f"Invalid URL: {value}") from e

        r = requests.get(value, timeout=self.timeout)

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise DataImportError(e) from e

        return r.json()
