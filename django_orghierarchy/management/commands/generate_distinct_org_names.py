from collections import Counter

from django.core.management.base import BaseCommand
from django_orghierarchy.models import Organization


class Command(BaseCommand):
    help = 'Generate distinct names for organizations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all', help='Generate distinct names for all orgs (not duplicates)', action='store_true',
        )

    def handle(self, *args, **options):
        # First we make sure the abbreviations are unique
        orgs = Organization.objects.filter(dissolution_date=None).select_related('parent')
        for org in orgs:
            if org.abbreviation:
                dupe_descendants = org.get_descendants().filter(abbreviation=org.abbreviation)
                for dupe in dupe_descendants:
                    print('%s (abbreviation %s -> None)' % (dupe, dupe.abbreviation))
                    dupe.abbreviation = None
                    dupe.save(update_fields=['abbreviation'])

        # Refresh from db
        orgs = Organization.objects.filter(dissolution_date=None).select_related('parent')
        orgs_by_name = {}
        for org in orgs:
            orgs_by_name.setdefault(org.name, []).append(org)

        for org_name, duplicate_orgs in orgs_by_name.items():
            if not options['all'] and len(duplicate_orgs) == 1:
                continue
            if len(duplicate_orgs) > 1:
                print("%d duplicates for %s" % (len(duplicate_orgs), org_name))

            if options['all']:
                levels = 4
            else:
                levels = 1
            # Keep on adding parent names until the names are distinct
            while levels < 5:
                distinct_names = [org.generate_distinct_name(levels) for org in duplicate_orgs]
                c = Counter(distinct_names)
                if max(c.values()) == 1:
                    break
                levels += 1

            for org in duplicate_orgs:
                distinct_name = org.generate_distinct_name(levels)
                print("\t%s" % distinct_name)
                if org.distinct_name != distinct_name:
                    org.distinct_name = distinct_name
                    org.save(update_fields=['distinct_name'])
