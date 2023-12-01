import datetime

import pytest
from pytest_django.asserts import assertQuerysetEqual

from django_orghierarchy.importers import DataImportError, RestAPIImporter
from django_orghierarchy.models import Organization, OrganizationClass
from django_orghierarchy.utils import get_data_source_model
from tests.factories import OrganizationFactory

req_mock = None


@pytest.fixture(autouse=True)
def global_requests_mock(requests_mock):
    global req_mock
    req_mock = requests_mock
    yield requests_mock

    req_mock = None


org_1 = {
    "abbreviation": "Hki",
    "classification": None,
    "created_at": "2014-11-27T20:06:22.404134",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": None,
    "id": "hel:00001",
    "name_fi": "Helsingin kaupunki",
    "name_sv": "Helsingfors stad",
    "origin_id": "00001",
    "parents": [],
    "policymaker": None,
    "resource_uri": "/paatokset/v1/organization/hel%3A00001/",
    "slug": "00001",
    "type": "city",
    "updated_at": "2014-11-27T20:06:22.408446",
}

org_2 = {
    "abbreviation": "Kvsto",
    "classification": None,
    "created_at": "2014-11-27T20:06:22.618886",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": None,
    "id": "hel:02900",
    "name_fi": "Kaupunginvaltuusto",
    "name_sv": "Stadsfullmäktige",
    "origin_id": "02900",
    "parents": ["/paatokset/v1/organization/hel%3A00001/"],
    "policymaker": "/paatokset/v1/policymaker/5/",
    "policymaker_slug": "kvsto",
    "resource_uri": "/paatokset/v1/organization/hel%3A02900/",
    "slug": "kvsto",
    "type": "council",
    "updated_at": "2017-08-03T11:42:34.949991",
}
org_3 = {
    "abbreviation": "Khs",
    "classification": None,
    "created_at": "2014-11-27T20:06:23.355894",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": None,
    "id": "hel:00400",
    "name_fi": "Kaupunginhallitus",
    "name_sv": "Stadsstyrelsen",
    "origin_id": "00400",
    "parents": ["/paatokset/v1/organization/hel%3A02900/"],
    "policymaker": "/paatokset/v1/policymaker/2/",
    "policymaker_slug": "khs",
    "resource_uri": "/paatokset/v1/organization/hel%3A00400/",
    "slug": "khs",
    "type": "board",
    "updated_at": "2017-08-03T11:42:34.961049",
}
org_4 = {
    "abbreviation": "Keha",
    "classification": None,
    "created_at": "2017-08-03T11:42:42.491738",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": "2017-06-01",
    "id": "hel:U50",
    "name_fi": "Keskushallinto",
    "name_sv": "Centralförvaltningen",
    "origin_id": "U50",
    "parents": ["/paatokset/v1/organization/hel%3A00400/"],
    "policymaker": None,
    "resource_uri": "/paatokset/v1/organization/hel%3AU50/",
    "slug": "u50",
    "type": "field",
    "updated_at": "2017-08-03T11:42:42.493469",
}
org_kanslia = {
    "abbreviation": "Kanslia",
    "classification": None,
    "created_at": "2017-08-03T11:42:42.566923",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": "2018-01-15",
    "id": "hel:U02100",
    "name_fi": "Kaupunginkanslia",
    "name_sv": "Stadskansliet",
    "origin_id": "U02100",
    "parents": ["/paatokset/v1/organization/hel%3AU50/"],
    "policymaker": None,
    "resource_uri": "/paatokset/v1/organization/hel%3AU02100/",
    "slug": "u02100",
    "type": "packaged_service",
    "updated_at": "2018-02-13T14:06:14.671597",
}
org_talpa = {
    "abbreviation": "Talpa",
    "classification": None,
    "created_at": "2017-08-03T11:42:42.526192",
    "deleted": False,
    "dissolution_date": None,
    "founding_date": "2020-03-01",
    "id": "hel:U01600",
    "name_fi": "Taloushallintopalveluliikelaitos",
    "name_sv": "Affärsverket ekonomiförvaltningen",
    "origin_id": "U01600",
    "parents": ["/paatokset/v1/organization/hel%3AU50/"],
    "policymaker": None,
    "resource_uri": "/paatokset/v1/organization/hel%3AU01600/",
    "slug": "u01600",
    "type": "packaged_service",
    "updated_at": "2022-11-03T16:03:58.790299",
}


def register_responses():
    response_1 = {
        "meta": {
            "limit": 3,
            "next": "/organization/?limit=3&offset=3",
            "offset": 0,
            "previous": None,
            "total_count": 6,
        },
        "objects": [org_1, org_2, org_3],
    }
    response_2 = {
        "meta": {
            "limit": 3,
            "next": None,
            "offset": 3,
            "previous": "/organization/?limit=3&offset=0",
            "total_count": 6,
        },
        "objects": [org_4, org_kanslia, org_talpa],
    }

    req_mock.get("http://fake.url/organization/", json=response_1)
    req_mock.get("http://fake.url/organization/?limit=3&offset=3", json=response_2)


@pytest.fixture
def importer():
    register_responses()
    return RestAPIImporter(
        "http://fake.url/organization/", RestAPIImporter.openahjo_config
    )


def test_expected_importer_configuration(importer):
    assert importer.has_meta
    assert importer.next_key == "next"
    assert importer.results_key == "objects"
    assert importer.default_data_source == "OpenAhjoAPI"

    expected_field_config = {
        "classification": {"source_field": "type"},
        "name": {"source_field": "name_fi"},
        "origin_id": {"data_type": "str_lower"},
        "parent": {
            "data_type": "org_id_regex",
            "optional": True,
            "pattern": r"\/(\w+:\w+)\/$",
            "source_field": "parents",
            "unquote": True,
            "unwrap_list": True,
        },
    }
    assert importer.field_config == expected_field_config


def test_data_iter(importer):
    """Test that data_iter returns all items from the API."""
    iterator = importer._data_iter(importer.url)
    assert len(list(iterator)) == 6


@pytest.mark.parametrize(
    "resource_id,expected",
    [
        (
            "/organization/?limit=20&offset=20",
            "http://fake.url/organization/?limit=20&offset=20",
        ),
        ("123", "http://fake.url/organization/123"),
        (
            "https://identifier-with-host/paatokset/v1/organization/?limit=20",
            "https://identifier-with-host/paatokset/v1/organization/?limit=20",
        ),
    ],
)
def test_build_resource_url(importer, resource_id, expected):
    assert importer._build_resource_url(resource_id) == expected


@pytest.mark.django_db
def test_import_organization_class(importer):
    """Test that organization class is imported correctly.

    Currently supported types in Open Ahjo API:
    https://github.com/City-of-Helsinki/openahjo/blob/master/decisions/models.py#L11
    - council,
    - board,
    - board_division,
    - committee,
    - field,
    - department,
    - division,
    - introducer,
    - introducer_field,
    - office_holder,
    - trustee,
    - city,
    - unit
    """
    organization_class = importer._import_organization_class(org_1["type"])

    qs = OrganizationClass.objects.all()
    assertQuerysetEqual(qs, [organization_class])
    assert organization_class.id == f"{importer.default_data_source}:city"
    assert organization_class.name == f"{importer.default_data_source}:city"


@pytest.mark.django_db
def test_import_organization_class_with_remapped_data_source(
    importer,
):
    importer.config["rename_data_source"] = {
        f"{importer.default_data_source}": "remapped"
    }

    organization_class = importer._import_organization_class(org_1["type"])

    qs = OrganizationClass.objects.all()
    assertQuerysetEqual(qs, [organization_class])
    assert organization_class.id == "remapped:city"
    assert organization_class.name == "remapped:city"


@pytest.mark.django_db
def test_import_data_source(importer):
    """OpenAhjo API doesn't define a data source, so we use the default one."""
    data_source = importer._import_data_source(importer.default_data_source)

    data_source_model = get_data_source_model()
    qs = data_source_model.objects.all()
    assertQuerysetEqual(qs, [data_source])
    assert data_source.id == f"{importer.default_data_source}"


@pytest.mark.django_db
def test_import_data_source_with_remapped_identifier(importer):
    """Remapping the default data source."""
    importer.config["rename_data_source"] = {
        f"{importer.default_data_source}": "remapped"
    }

    data_source = importer._import_data_source(importer.default_data_source)

    data_source_model = get_data_source_model()
    qs = data_source_model.objects.all()
    assertQuerysetEqual(qs, [data_source])
    assert data_source.id == "remapped"


@pytest.mark.django_db
def test_import_data(importer):
    importer.import_data()
    data_source_model = get_data_source_model()
    assert Organization.objects.count() == 6
    assert data_source_model.objects.count() == 1
    assert OrganizationClass.objects.count() == 5


@pytest.mark.django_db
def test_import_organization_data(importer):
    importer.import_data()

    organization = Organization.objects.get(
        id=f"{importer.default_data_source}:{org_kanslia['origin_id'].lower()}"
    )
    assert organization.name == org_kanslia["name_fi"]
    assert (
        organization.classification.id
        == f"{importer.default_data_source}:packaged_service"
    )
    assert organization.data_source.id == f"{importer.default_data_source}"
    assert organization.origin_id == org_kanslia["origin_id"].lower()
    assert organization.founding_date == datetime.date(2018, 1, 15)
    assert organization.dissolution_date is None


@pytest.mark.django_db
def test_import_organization_data_with_remapped_data_source(importer):
    importer.config["rename_data_source"] = {
        f"{importer.default_data_source}": "remapped"
    }

    importer.import_data()

    organization = Organization.objects.get(
        id=f"remapped:{org_kanslia['origin_id'].lower()}"
    )
    assert organization.name == org_kanslia["name_fi"]
    assert organization.classification.id == "remapped:packaged_service"
    assert organization.data_source.id == "remapped"
    assert organization.origin_id == org_kanslia["origin_id"].lower()
    assert organization.founding_date == datetime.date(2018, 1, 15)
    assert organization.dissolution_date is None


@pytest.mark.django_db
def test_import_organization_with_parent(importer):
    importer.import_data()

    org_child = Organization.objects.get(
        id=f"{importer.default_data_source}:{org_kanslia['origin_id'].lower()}"
    )
    org_parent = Organization.objects.get(
        id=f"{importer.default_data_source}:{org_4['origin_id'].lower()}"
    )
    assert org_child.parent == org_parent


@pytest.mark.django_db
def test_import_organization_without_parent(importer):
    organization = importer._import_organization(org_1)

    qs = Organization.objects.all()
    assertQuerysetEqual(qs, [organization])
    assert organization.name == org_1["name_fi"]
    assert (
        organization.id
        == f"{importer.default_data_source}:{org_1['origin_id'].lower()}"
    )


@pytest.mark.django_db
def test_import_organization_flip_parents(importer):
    """Create organization with different parent organization than in the data and
    check that importing updates the parent organization."""
    organization_kanslia = OrganizationFactory(
        name="existing-organization",
        origin_id=org_kanslia["origin_id"].lower(),
        data_source=importer._import_data_source(importer.default_data_source),
    )

    organization_4 = OrganizationFactory(
        name="existing-organization",
        origin_id=org_4["origin_id"].lower(),
        data_source=importer._import_data_source(importer.default_data_source),
        parent=organization_kanslia,
    )

    importer.import_data()

    organization_kanslia.refresh_from_db()
    organization_4.refresh_from_db()

    assert organization_kanslia.parent == organization_4


@pytest.mark.django_db
def test_import_organization_update_existing(importer):
    organization = OrganizationFactory(
        name="existing-organization",
        origin_id=org_kanslia["origin_id"].lower(),
        data_source=importer._import_data_source(importer.default_data_source),
    )

    importer._import_organization(org_kanslia)

    organization.refresh_from_db()
    assert organization.name == org_kanslia["name_fi"]
    assert (
        organization.classification.id
        == f"{importer.default_data_source}:packaged_service"
    )
    assert organization.parent.name == org_4["name_fi"]
    assert organization.dissolution_date is None
    assert organization.founding_date == datetime.date(2018, 1, 15)


@pytest.mark.parametrize("skip_classifications", [True, False])
@pytest.mark.django_db
def test_import_organization_data_with_skip_classifications(
    importer, skip_classifications
):
    """Organization is not imported if it's in the classification skip list."""
    if skip_classifications:
        importer.config["skip_classifications"] = ["city"]

    importer.import_data()

    assert (
        Organization.objects.filter(origin_id__iendswith=org_1["origin_id"]).count()
        == 0
        if skip_classifications
        else 1
    )


@pytest.mark.parametrize(
    "value,unwrap,expected",
    [
        ([], True, None),
        (["identifier"], True, "identifier"),
        (["identifier1", "identifier2"], True, "identifier1"),
        ([], False, []),
        (["identifier"], False, ["identifier"]),
        (["identifier1", "identifier2"], False, ["identifier1", "identifier2"]),
    ],
)
def test_get_field_value_unwrap(importer, value, unwrap, expected):
    config = {"unwrap_list": unwrap}
    value = importer._get_field_value({"origin_id": value}, "origin_id", config)
    assert value == expected
    if expected is None:
        assert value is None


@pytest.mark.parametrize(
    "value,unquote,expected",
    [("a%3Ab%25c%23d", True, "a:b%c#d"), ("a%3Ab%25c%23d", False, "a%3Ab%25c%23d")],
)
def test_get_field_value_unquote(importer, value, unquote, expected):
    config = {
        "unquote": unquote,
    }
    value = importer._get_field_value({"origin_id": value}, "origin_id", config)
    assert value == expected


@pytest.mark.django_db
def test_get_field_value_org_id_regex_data_type(importer):
    """Parses organization id from a string using regex pattern."""
    config = {
        "source_field": "parents",
        "data_type": "org_id_regex",
        "unwrap_list": True,
        "unquote": True,
        "optional": True,
    }

    # test raise DataImportError if no pattern is provided
    with pytest.raises(DataImportError):
        importer._get_field_value(org_2, "parent", config)

    config["pattern"] = r"\/(\w+:\w+)\/$"

    # This should import the parent organization
    value = importer._get_field_value(org_2, "parent", config)
    assert isinstance(value, Organization)
    assert value.name == org_1["name_fi"]
