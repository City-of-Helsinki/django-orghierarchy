from django.contrib.auth import get_user_model


def make_admin(username='testadmin', is_superuser=True):
    user_model = get_user_model()
    return user_model.objects.create(username=username, is_staff=True, is_superuser=is_superuser)


def clear_user_perm_cache(user):
    # permission cache, when empty, evaluates to False, but must be deleted anyway
    if getattr(user, '_user_perm_cache', None) is not None:
        delattr(user, '_user_perm_cache')
    if getattr(user, '_perm_cache', None) is not None:
        delattr(user, '_perm_cache')
