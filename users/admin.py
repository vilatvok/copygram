from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Action, Block, Follower, User


@admin.register(User)
class UserAdm(UserAdmin):
    list_display = ["username", "is_superuser"]
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            ("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone", "avatar")},
        ),
        (
            ("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ["user_from", "user_to"]
    list_display_links = ["user_from", "user_to"]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ["block_from", "block_to"]
    list_display_links = ["block_from", "block_to"]


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "act", "date"]
