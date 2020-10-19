import copy

from django.core.management.base import BaseCommand, CommandError

from django_orghierarchy.importers import DataImportError, RestAPIImporter


class Command(BaseCommand):
    help = 'Import organization data from a REST API'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            metavar='URL',
            help='REST API endpoint from where the organization data will be imported',
        )

        parser.add_argument(
            '-s',
            '--rename-data-source',
            dest='rename_data_source',
            nargs='+',
            default=['helsinki:ahjo'],
            help='Rename data sources. Renaming should be specified as <old_identifier>:<new_identifier>'
        )

        parser.add_argument(
            '-c',
            '--config',
            dest='config',
            default='paatos',
            choices=['paatos', 'tprek'],
            help='REST API configuration to use when importing.'
        )

    def _parse_rename_data_source(self, value):
        try:
            old_name, new_name = value.split(':')
        except ValueError:
            raise CommandError(
                'Invalid data source renaming. Renaming should be specified as <old_identifier>:<new_identifier>'
            )

        return old_name.strip(), new_name.strip()

    def handle(self, *args, **options):
        url = options['url']

        config = {}
        if options['config']:
            config = copy.deepcopy(getattr(RestAPIImporter, '%s_config' % options['config']))
        if options['rename_data_source']:
            rename_data_source = {}
            for item in options['rename_data_source']:
                old_name, new_name = self._parse_rename_data_source(item)
                rename_data_source[old_name] = new_name
            config['rename_data_source'] = rename_data_source

        importer = RestAPIImporter(url, config)
        try:
            importer.import_data()
        except DataImportError as e:
            self.stderr.write('Import failed: {0}'.format(e))
        else:
            self.stdout.write('Import completed successfully')
