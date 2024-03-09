from django.contrib import admin

from chat.models import Message, RoomChat, MessageImages


@admin.register(RoomChat)
class RoomChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created', 'users_count']

    @admin.display(description='Count users')
    def users_count(self, room: RoomChat):
        return room.users.count()
    

admin.site.register(Message)
admin.site.register(MessageImages)
