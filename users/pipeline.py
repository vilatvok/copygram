from django.contrib.auth.models import Group


def new_users_handler(backend, user, response, *args, **kwargs):
    """
    The user, who was logged in through social, 
    is forbidden to change the password.
    """
    group = Group.objects.get(name='social')
    if group:
        user.groups.add(group)