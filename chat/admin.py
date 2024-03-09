from django.contrib import admin

from chat.models import RoomChat, PrivateChat


@admin.register(RoomChat)
class RoomChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created', 'users_count']

    @admin.display(description='Count users')
    def users_count(self, room: RoomChat):
        return room.users.count()
    

admin.site.register(PrivateChat)
