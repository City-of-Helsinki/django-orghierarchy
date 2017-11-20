from django.core.management.base import BaseCommand

from django_orghierarchy.importers import DataImportError, RestAPIImporter


class Command(BaseCommand):
    help = 'Import organization data from a REST API'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            metavar='URL',
            help='REST API endpoint from where the organization data will be imported',
        )

    def handle(self, *args, **options):
        url = options['url']
        importer = RestAPIImporter(url)
        try:
            importer.import_data()
        except DataImportError as e:
            self.stderr.write('Import failed: {0}'.format(e))
        else:
            self.stdout.write('Import completed successfully')
