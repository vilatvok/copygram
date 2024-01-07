from django.contrib import admin
from .models import Post, Comment, Story


# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["owner", "description", "date", "is_comment", "leng"]
    list_display_links = ["description"]
    list_filter = ["owner", "date"]
    search_fields = ["description"]
    actions = ["com_on", "com_off"]

    @admin.display(description="Length")
    def leng(self, post: Post):
        return f"length of description - {len(post.description)}"

    @admin.action(description="Comment on")
    def com_on(self, request, queryset):
        queryset.update(is_comment=True)

    @admin.action(description="Comment off")
    def com_off(self, request, queryset):
        queryset.update(is_comment=False)
        self.message_user(request, "Off")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["owner", "post", "date", "text"]
    list_display_links = ["owner", "post"]
    list_filter = ["owner", "date"]


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    fields = ["owner", "img"]
