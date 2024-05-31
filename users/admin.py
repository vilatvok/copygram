from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import (
    Action,
    Archive,
    Block,
    Follower,
    Report,
    User,
    UserPrivacy,
)


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


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('id', 'target')
    list_filter = ('target',)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'date',
        'act',
        'object_id',
        'file',
        'unread',
    )
    list_filter = ('owner', 'date', 'unread')
    readonly_fields = ('unread',)
    autocomplete_fields = ('owner',)


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
    list_display = ('id', 'report_from', 'report_on', 'date')
    list_filter = ('report_from', 'report_on', 'date')


@admin.register(UserPrivacy)
class UserPrivacyAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'private_account',
        'comments',
        'likes',
        'online_status',
    )
    list_editable = ('private_account', 'comments', 'likes', 'online_status')
