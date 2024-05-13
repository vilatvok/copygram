# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import RoomChat, PrivateChat, Message, MessageImages


@admin.register(RoomChat)
class RoomChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'image', 'name', 'created')
    list_filter = ('owner', 'created')
    search_fields = ('name',)


@admin.register(PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_user', 'second_user')
    list_filter = ('first_user', 'second_user')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'content',
        'timestamp',
        'content_type',
        'object_id',
    )
    list_filter = ('user', 'timestamp', 'content_type')


@admin.register(MessageImages)
class MessageImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file')
    list_filter = ('message',)
