from django.contrib.auth import get_user_model


def make_admin(username='testadmin'):
    user_model = get_user_model()
    return user_model.objects.create(username=username, is_staff=True, is_superuser=True)
