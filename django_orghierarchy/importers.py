import copy
import logging
import re
from enum import Enum

import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from .models import OrganizationClass, Organization
from .utils import get_data_source_model

logger = logging.getLogger(__name__)


class DataImportError(Exception):
    pass


class DataType(Enum):
    VALUE = 'value'
    STR_LOWER = 'str_lower'
    LINK = 'link'
    REGEX = 'regex'


class RestAPIImporter:
    """This class allows importing organization data from a REST API endpoint. The default
    configuration supports the 6aika Open Decision API specification:
    https://github.com/6aika/api-paatos

    The importer will also create data sources and organization classes if does not exist.
    If a single value is provided to `data_source` and `classification` fields, then the
    importer assumes the value is the name of the data source or organization class. If
    an object (dict) is provided to `data_source` and `classification` fields, then the
    importer will create objects with object data. Either full object data or a link to
    full object data should be provided to parent field so that the importer can create
    parent organization before creating child organization.

    For use in multi-source setups, the importer may optionally create a parent organization
    for the data source that is the common parent of all imported top-level organizations.
    This way, separate organization hierarchies from different data sources may be stored
    in the same application.

    The client code can override the default config or pass in a config object to allow
    the importer parsing different REST API structures.

    Config options:
        - next_key: The url to the next page if the source data is paginated, or None if not.
        - results_key: The object key to the list of organization objects, or None if the list is at
            root level.
        - fields: The fields of which the values will be imported. The same fields will be imported
            in organization classes, if present.
        - update_fields: The fields to update if the organization with same origin_id and data
            source exists.
        - field_config: Configs for each field. Config options:
            - source_field: The source data object key where the field value comes from.
                Defaults to original field name.
            - data_type: The data type for the field, can be 'value', 'str_lower', 'link' or 'regex'.
                Defaults to 'value'. If the data type is 'value', it will return the value
                from source data; if the data type is 'str_lower', it will return the value stringified
                and lowercased; if the data type is 'link', it will return the data fetched
                from the link; if the data type is 'regex', it will return the value extracted
                from the given pattern.
            - optional: Whether the importer will continue if the field is missing.
                Defaults to False.
        - rename_data_source: Data sources that are renamed during import.
        - default_data_source: Data source id to use for objects without data source.
        - default_parent_organization: If set, name of the parent organization to be created for all
            imported top level organizations.

    Example config:
        {
            'next_key': 'next',
            'results_key: 'results',
            'fields': ['origin_id', 'data_source', 'classification'],
            'update_fields': ['classification'],
            'field_config': {
                'origin_id': {
                    'source_field': 'id',
                    'data_type': 'regex',
                    'pattern': r'abc:(\d+)',
                },
                'parent': {
                    'data_type': 'link',
                }
            },
            'rename_data_source': {
                'original_name_1': 'new_name_1',
                'original_name_2': 'new_name_2',
            },
            'default_data_source': 'new_name_1',
            'default_parent_organization': None
        }
    """

    paatos_config = {
        'next_key': 'next',
        'results_key': 'results',
        'fields': [
            'data_source', 'origin_id', 'classification',
            'name', 'founding_date', 'dissolution_date',
            'parent',
        ],
        'update_fields': [
            'classification', 'name', 'founding_date',
            'dissolution_date', 'parent',
        ],
        'field_config': {
            'parent': {
                'data_type': 'link',
            },
            'origin_id': {
                'data_type': 'str_lower',
            }
        },
        'default_data_source': 'OpenDecisionAPI'
    }

    tprek_config = {
        'next_key': None,
        'results_key': None,
        'fields': [
            'origin_id', 'classification',
            'name', 'parent',
        ],
        'update_fields': [
            'classification', 'name', 'parent',
        ],
        'field_config': {
            'parent': {
                'source_field': 'parent_id',
                'data_type': 'value',
                'optional': True,
            },
            'origin_id': {
                'source_field': 'id',
                'data_type': 'value',
            },
            'classification': {
                'source_field': 'organization_type',
                'optional': True,
            },
            'name': {
                'source_field': 'name_fi',
                'optional': True,
            }
        },
        'default_data_source': 'tprek',
        'default_parent_organization': 'Pääkaupunkiseudun toimipisterekisteri'
    }

    default_config = paatos_config

    def __init__(self, url, config=None):
        self.url = url

        self.config = copy.deepcopy(self.default_config)
        config = copy.deepcopy(config)
        if config:
            # only consider fields listed in given config when merging field configs
            default_field_config = self.config.pop('field_config')
            given_field_config = config.pop('field_config')
            merged_field_config = {}
            for field in config.get('fields', None):
                if field in given_field_config:
                    merged_field_config[field] = given_field_config[field]
                elif field in default_field_config:
                    merged_field_config[field] = default_field_config[field]
            self.config['field_config'] = merged_field_config
            self.config.update(config)
        logger.info('Importing organization data from %s with the following config:' % self.url)
        logger.info(self.config)
        self.related_import_methods = {
            'data_source': self._import_data_source,
            'classification': self._import_organization_class,
            'parent': self._import_organization,
        }

        self._organization_classes = {}
        self._data_sources = {}
        self._default_parent = None
        if self.config.get('default_parent_organization', None):
            origin_id_config = self.config['field_config'].get('origin_id', None)
            origin_id_field = origin_id_config['source_field'] if origin_id_config else 'origin_id'
            data_source_config = self.config['field_config'].get('data_source', None)
            data_source_field = data_source_config['source_field'] if data_source_config else 'data_source'
            name_config = self.config['field_config'].get('name', None)
            name_field = name_config['source_field'] if name_config else 'name'
            default_parent_data = {
                origin_id_field: self.config['default_data_source'],
                data_source_field: self.config['default_data_source'],
                name_field: self.config['default_parent_organization']
            }
            self._default_parent = self._import_organization(default_parent_data)

    @property
    def fields(self):
        return self.config['fields']

    @property
    def update_fields(self):
        return self.config['update_fields']

    @property
    def field_config(self):
        return self.config['field_config']

    @property
    def next_key(self):
        """Object key that stores the link to the next page"""
        return self.config['next_key']

    @property
    def results_key(self):
        """Object key that stores the list of organizations"""
        return self.config['results_key']

    @property
    def rename_data_source(self):
        """Data source renaming configs"""
        return self.config.get('rename_data_source') or {}

    @property
    def default_data_source(self):
        """Default data source string"""
        return self.config['default_data_source']

    def _get_organization_class(self, data):
        """Get organization class for the given object data

        The method will first try to get the organization class from cache, and
        then get from database if not cached.
        """
        # organization class supports id, data_source, origin_id and name.
        supported_fields = {'id', 'origin_id', 'data_source', 'name'}
        identifier = data.get('id')
        # organization class requires data source and origin_id.
        if isinstance(identifier, str) and ':' in identifier:
            if 'data_source' not in data:
                data['data_source'] = identifier.split(':')[0]
            if 'origin_id' not in data:
                data['origin_id'] = identifier.split(':')[1]
        # provided id used if origin id missing
        if 'origin_id' not in data or not data['origin_id']:
            data['origin_id'] = identifier
        # default data source used if missing
        if 'data_source' not in data or not data['data_source']:
            data['data_source'] = self.default_data_source
        # reformat id to fit our model
        if not isinstance(identifier, str) or ':' not in identifier:
            data['id'] = data['data_source'] + ':' + str(identifier)
        data['data_source'] = self.related_import_methods['data_source'](data['data_source'])
        # extra fields should not crash the import. Only use specified fields.
        data = {field: value for (field, value) in data.items() if field in supported_fields}
        if identifier not in self._organization_classes:
            organization_class, _ = OrganizationClass.objects.get_or_create(**data)
            self._organization_classes[identifier] = organization_class
        return self._organization_classes[identifier]

    def _get_data_source(self, data):
        """Get data source for the given object data

        The method will first try to get the data source from cache, and
        then get from database if not cached.
        """
        identifier = data['id']

        if identifier in self.rename_data_source:
            identifier = self.rename_data_source[identifier]
            data['id'] = identifier

        if identifier not in self._data_sources:
            data_source_model = get_data_source_model()
            data_source, _ = data_source_model.objects.get_or_create(**data)
            self._data_sources[identifier] = data_source
        return self._data_sources[identifier]

    def import_data(self):
        """Import data"""
        for data_item in self._data_iter(self.url):
            self._import_organization(data_item)

    @transaction.atomic
    def _import_organization(self, data):
        """Import single organization.

        The organization import is transactional so, for example, we do not
        accidentally save organization without parent if the parent organization
        saving failed for some reason.

        If a single value is provided to organization field, we assume it's
        the id of the organization. This requires that all fields apart from id
        must be marked *not* required in the config.
        """
        # id must always be present
        config = self.field_config.get('origin_id') or {}
        if isinstance(data, dict):
            incoming_data = data
        elif isinstance(data, str):
            # we are only referring to id. The organization might already exist, or it is imported later.
            incoming_data = {config['source_field']: data} if config.get('source_field') else {'origin_id': data}
        else:
            raise DataImportError('Organization data must be dict or an organization id.')
        origin_id = self._get_field_value(incoming_data, 'origin_id', config)

        # data source may be missing altogether, or it may be optional
        data_source = None
        config = self.field_config.get('data_source') or {}
        try:
            data_source = self._get_field_value(incoming_data, 'data_source', config)
        except DataImportError as exception:
            if not config or config.get('optional'):
                pass
            else:
                raise exception
        if not data_source:
            data_source = self._get_field_value(
                {'data_source': self.default_data_source}, 'data_source', {'data_type': 'value'})

        # id is never imported in default config

        try:
            # enforce lower case id standard, but recognize upper case ids as equal:
            organization = Organization.objects.get(origin_id__iexact=origin_id, data_source=data_source)
            logger.info('Organization already exists: {0}'.format(organization.id))

            for field in self.update_fields:
                config = self.field_config.get(field) or {}
                try:
                    value = self._get_field_value(incoming_data, field, config)
                except DataImportError as exception:
                    if config.get('optional'):
                        continue
                    else:
                        raise exception
                setattr(organization, field, value)
            if (
                self.config.get('default_parent_organization', None)
                and not organization.parent
                and organization != self._default_parent
            ):
                organization.parent = self._default_parent
            organization.save()

            return organization
        except Organization.DoesNotExist:
            object_data = {'origin_id': origin_id, 'data_source': data_source}
            for field in self.fields:
                config = self.field_config.get(field) or {}
                try:
                    object_data[field] = self._get_field_value(incoming_data, field, config)
                except DataImportError as exception:
                    if config.get('optional'):
                        continue
                    else:
                        raise exception
            organization = Organization.objects.create(**object_data)
            if (
                self.config.get('default_parent_organization', None)
                and not organization.parent
                and organization != self._default_parent
            ):
                organization.parent = self._default_parent
                organization.save()
            return organization

    def _import_data_source(self, data):
        """Import data source

        If a single value is provided to data_source field, it assume it's
        the id of the data source.
        """
        if isinstance(data, dict):
            object_data = data
        else:
            object_data = {'id': data}

        return self._get_data_source(object_data)

    def _import_organization_class(self, data):
        """Import organization class.

        If a single value is provided to classification field, it assume it's
        the id of the organization class.

        If a dict is provided, origin_id is used if present, otherwise id.
        """
        if isinstance(data, dict):
            object_data = {k: v for k, v in data.items() if k != 'id'}
            object_data['id'] = data['origin_id'] if 'origin_id' in data else data['id']
        else:
            object_data = {'id': data}

        return self._get_organization_class(object_data)

    def _data_iter(self, url):
        """Iterate over data items in the REST API endpoint.

        The iterator will follow over next page links if available.
        """
        logger.info('Start importing data from {0} ...'.format(url))

        r = requests.get(url)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise DataImportError(e)

        data = r.json()
        for data_item in data[self.results_key] if self.results_key else data:
            yield data_item

        logger.info('Importing data from {0} completed'.format(url))

        if self.next_key and data[self.next_key]:
            next_url = data[self.next_key]
            yield from self._data_iter(next_url)

    def _get_field_value(self, data_item, field, config):
        """Get source value for the field from the data item

        If source_field is specified in field config, the source_field
        will be used to get the source value, otherwise the model field
        will be used.

        If the data type is DataType.VALUE, the value will be returned;
        If the data type is DataType.STR_LOWER, the value will be returned stringified to lower case;
        If the data type is DataType.LINK, the data in the link will be returned;
        If the data type is DataType.REGEX, the extracted value for the pattern will be returned.
        """
        source_field = config.get('source_field') or field
        try:
            value = data_item[source_field]
        except KeyError:
            raise DataImportError('Field not found in source data: {0}'.format(source_field))

        if not value:
            return value

        if config.get('data_type'):
            try:
                data_type = DataType(config['data_type'])
            except ValueError:
                raise DataImportError('Invalid data type: {0}. Supported data types are: {1}'.format(
                    config['data_type'],
                    ', '.join([e.value for e in DataType]),
                ))
        else:
            data_type = DataType.VALUE

        if data_type == DataType.STR_LOWER:
            value = str(value).lower()
        elif data_type == DataType.LINK:
            value = self._get_link_data(value)
        elif data_type == DataType.REGEX:
            try:
                pattern = config['pattern']
            except KeyError:
                raise DataImportError('No regex pattern provided for the field: {0}'.format(field))
            value = self._get_regex_data(value, pattern)

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
                'Cannot extract value from string {0} with pattern {1}'.format(value, pattern)
            )
        return data

    @staticmethod
    def _get_link_data(value):
        """Get data fetched from the link"""
        validator = URLValidator()
        try:
            validator(value)
        except ValidationError:
            raise DataImportError('Invalid URL: {0}'.format(value))

        r = requests.get(value)

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise DataImportError(e)

        return r.json()
