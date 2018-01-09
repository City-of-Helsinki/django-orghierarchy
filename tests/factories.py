import factory


class DataSourceFactory(factory.django.DjangoModelFactory):
    id = factory.Sequence(lambda n: "data-source-{0}".format(n))
    name = factory.Faker('text', max_nb_chars=255)

    class Meta:
        model = 'django_orghierarchy.DataSource'


class OrganizationClassFactory(factory.django.DjangoModelFactory):
    data_source = factory.SubFactory(DataSourceFactory)
    origin_id = factory.Faker('text', max_nb_chars=255)
    name = factory.Faker('text', max_nb_chars=255)

    class Meta:
        model = 'django_orghierarchy.OrganizationClass'


class OrganizationFactory(factory.django.DjangoModelFactory):
    data_source = factory.SubFactory(DataSourceFactory)
    origin_id = factory.Faker('text', max_nb_chars=255)
    classification = factory.SubFactory(OrganizationClassFactory)
    name = factory.Faker('text', max_nb_chars=255)

    class Meta:
        model = 'django_orghierarchy.Organization'
