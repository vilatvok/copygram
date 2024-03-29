from django.contrib import admin

from mainsite.models import Post, Comment, Story


# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'description', 'date', 'is_comment']
    list_filter = ['date']
    search_fields = ['description']
    actions = ['com_on', 'com_off']

    @admin.display(description='Length')
    def leng(self, post: Post):
        return f'length of description - {len(post.description)}'

    @admin.action(description='Comment on')
    def com_on(self, request, queryset):
        queryset.update(is_comment=True)

    @admin.action(description='Comment off')
    def com_off(self, request, queryset):
        queryset.update(is_comment=False)
        self.message_user(request, 'Off')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'post', 'date', 'text']
    list_filter = ['date']


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['owner', 'img']
