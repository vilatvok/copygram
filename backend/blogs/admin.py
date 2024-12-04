from django.contrib import admin
from django.utils.html import format_html

from blogs.models import Post, Comment, PostMedia, Story, UninterestingPost


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'description',
        'created_at',
        'is_comment',
        'archived',
    )
    list_filter = ('created_at',)
    list_editable = ('archived', 'is_comment')
    list_per_page = 30
    list_max_show_all = 100
    search_fields = ('description', 'id', 'owner__username')
    autocomplete_fields = ('owner',)
    actions = ('commments_on', 'comments_off')
    inlines = (PostMediaInline, CommentInline)
    list_per_page = 20

    @admin.action(description='Comments on')
    def comments_on(self, request, queryset):
        queryset.update(is_comment=True)

    @admin.action(description='Comments off')
    def comments_off(self, request, queryset):
        queryset.update(is_comment=False)
        self.message_user(request, 'Off')


@admin.register(UninterestingPost)
class UninterstingPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post')
    list_filter = ('user', 'post')
    search_fields = ('user__username', 'user__email')


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    def file_tag(self, obj):
        url = obj.file.url
        tag = f'<img src="{url}" style="max-witdh:200px; max-height:200px"/>'
        return format_html(tag)

    file_tag.short_description = 'File'

    list_per_page = 10
    list_display = ('id', 'post', 'file_tag')
    list_filter = ('post',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'created_at', 'post', 'parent', 'text')
    list_filter = ('owner', 'created_at', 'post')
    autocomplete_fields = ('owner', 'post')
    search_fields = ('text',)
    list_per_page = 20
    list_max_show_all = 100
    list_select_related = ('owner', 'post')


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    def img_tag(self, obj):
        url = obj.img.url
        tag = f'<img src="{url}" style="max-witdh:200px; max-height:200px"/>'
        return format_html(tag)

    img_tag.short_description = 'Image'

    list_display = ('id', 'owner', 'created_at', 'img_tag', 'archived')
    list_filter = ('created_at',)
    autocomplete_fields = ('owner',)
