import swapper


def get_data_source_model():
    """Get data source model being used"""
    return swapper.load_model('django_orghierarchy', 'DataSource')
