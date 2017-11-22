# django-orghierarchy

Reusable Django application for hierarchical organizations

## Development

### Tests

#### Unit tests

Run tests

    py.test

Run tests with coverage report

    py.test --cov-report html --cov .
    
Open htmlcov/index.html for the coverage report.

#### Integration tests

We need to provide different settings files for the test as the
setting variables for swappable model are only evaluated the first
time the module is imported.

Run tests

    python manage.py test --tag=custom_ds --settings=tests.test_app.settings_custom_ds
    python manage.py test --tag=custom_pk_ds --settings=tests.test_app.settings_custom_pk_ds


## Import Organization Data

Import organization data from a REST API endpoint

    python manage.py import_organizations "http://example.com/v1/organization/"
    
If the data source needs to be renamed, provides a new data source name to replace the old one:

    python manage.py import_organizations "http://example.com/v1/organization/" -s old_name:new_name
