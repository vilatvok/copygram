from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Action, Block, Follower, Report, User, UserPrivacy


@admin.register(User)
class UserAdmin(UserAdmin):
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
                'gender',
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
        (
            ('Important dates'),
            {'fields': (
                'last_login',
                'date_joined',
                'last_activity',
                'is_online',
            )}
        ),
    )
    prepopulated_fields = {'slug': ['username']}


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'date',
        'act',
        'file',
        'unread',
        'content_type',
        'object_id',
    )
    list_filter = ('owner', 'date', 'unread', 'content_type')


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user')
    list_filter = ('from_user', 'to_user')


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'block_from', 'block_to')
    list_filter = ('block_from', 'block_to')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_from', 'report_on')


@admin.register(UserPrivacy)
class UserPrivacyAdmin(admin.ModelAdmin):
    list_display = ('user',)
