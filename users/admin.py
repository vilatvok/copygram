from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Action, Block, Follower, User


@admin.register(User)
class UserAdmim(UserAdmin):
    list_display = ['id', 'username', 'email', 'is_superuser']
    fieldsets = (
        (None, {'fields': ('slug', 'username', 'password')}),
        (
            ('Personal info'),
            {'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'avatar', 
                'bio', 
                'gender'
            )},
        ),
        (
            ('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (('Important dates'), 
        {'fields': (
            'last_login', 
            'date_joined', 
            'last_activity', 
            'private_account', 
            'is_online'
        )}),
    )
    prepopulated_fields = {'slug': ['username']}


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_from', 'user_to']


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'block_from', 'block_to']


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'act', 'date']
