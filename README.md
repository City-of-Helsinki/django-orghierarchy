# django-orghierarchy

Reusable Django application for hierarchical organizations

# Installation

1. `pip install django-orghierarchy`

2. Add `django_orghierarchy` to `INSTALLED_APPS`

3. If you wish to use your own Django model as data source model (the same way you hot-swap your own user model in Django), add `DJANGO_ORGHIERARCHY_DATASOURCE_MODEL = 'yourapp.DataSource'` to your project settings. Otherwise, the barebones Django model `DataSource` at django_orghierarchy/models.py is used, it contains the fields a data source model *must* contain to be used with django-orghierarchy. Similarly, django-orghierarchy links to your user model, so `AUTH_USER_MODEL` must be defined in Django project settings as always.

4. Run migrations

 ```bash
 python manage.py migrate django_orghierarchy
 ```


# Usage

The `Organization` class is the main feature of django-orghierarchy. We use [`django-mptt`](https://github.com/django-mptt/django-mptt/) to implement an organization hierarchy that can be as deep as you wish. Each organization has a name, a data source (referring to the system the organization data is from), origin_id (referring to organization id in the original data source), founding date and dissolution date, status (*normal* or *affiliated*), a place in a forest of organization trees, and possibly a *replacement organization*, which means a link to any other organization across the trees (making the forest strictly a directed graph, not a bunch of trees). Replacement organization allows linking dissolved organization structures to new ones so that old user rights are automatically transferred across the hierarchy to the replacing organization.

Each organization may have `admin_users` and `regular_users`, which are linked to your Django user model. Also, an organization may have `sub_organizations` and `affiliated_organizations`. You may have any number of top level organizations. Also, some extra user permissions are defined, i.e. `add_affiliated_organization`, `change_affiliated_organization`, `delete_affiliated_organization`, `replace_organization` and `change_organization_regular_users`. These permissions are for adding *regular users* and *affiliated organizations* in Django-admin, and creating *replacement* links, without being allowed to touch the *admin users* or the existing organization hierarchy. *Affiliated* organizations usually have more limited rights than *normal* organizations within the hierarchy; they are meant for external organizations you collaborate with and wish to grant limited rights to.

Your desired user rights and permissions for each user group in each level of the organization depend on your application details, so you should implement your own user rights checks depending on your needs. You may e.g. create a user model permissions mixin that uses information on the user organization, as done in [Linkedevents permissions](https://github.com/City-of-Helsinki/linkedevents/blob/master/events/permissions.py) and [Linkedevents user model](https://github.com/City-of-Helsinki/linkedevents/blob/master/helevents/models.py). The user rights model is originally specified [here](https://github.com/City-of-Helsinki/linkedevents/issues/235).

You may import an existing organization hierarchy from a REST API corresponding to the [6Aika Paatos decisionmaking API specification](https://github.com/6aika/api-paatos), based on the [Popolo project](http://www.popoloproject.com/), with the included importer, for example:
```bash
python manage.py import_organizations "https://api.hel.fi/paatos/v1/organization/"
```

You may give the organization data source a specific id to correspond to your own data source model ids in your project:
```bash
python manage.py import_organizations "https://api.hel.fi/paatos/v1/organization/" -s original_id:imported_id
```

Otherwise, the data source id in the original API is used for the imported organizations (`helsinki` in the Helsinki API).


# Development

Install requirements.

```bash
# Package requirements
pip install -e .
# Development requirements
pip install -r requirements.txt
```


## Tests


### Unit tests

Run the tests.

```bash
pytest
```

Run the tests with coverage report.

```bash
pytest --cov-report html --cov .
```

Open htmlcov/index.html for the coverage report.


### Running tests against multiple environments

You can run the tests against multiple environments by using [tox](https://tox.readthedocs.io/en/latest/).
Install `tox` globally and run:

```bash
tox
```

Use the `-f` option to specify target environments.

```bash
# Target only Python 3.9 environments
tox -f py39
# Target Python 3.9 and Django 4.2
tox -f py39 django42
```


### Integration tests

We need to provide different settings files for the test as the
setting variables for swappable model are only evaluated the first
time the module is imported. Integration tests are skipped by default.

Run the integration tests.
```bash
pytest -m custom_ds --ds=tests.test_app.settings_custom_ds
pytest -m custom_pk_ds --ds=tests.test_app.settings_custom_pk_ds
```


## Code format

This project uses
[`ruff`](https://github.com/astral-sh/ruff)
for code formatting and quality checking. Ruff configuration is to be found
in `pyproject.toml`.

Basic `ruff` commands:

* To let `ruff` do its magic: `ruff format` and `ruff check --fix`

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.


## Git blame ignore refs

Project includes a `.git-blame-ignore-revs` file for ignoring certain commits from `git blame`.
This can be useful for ignoring e.g. formatting commits, so that it is more clear from `git blame`
where the actual code change came from. Configure your git to use it for this project with the
following command:

```shell
git config blame.ignoreRevsFile .git-blame-ignore-revs
```
