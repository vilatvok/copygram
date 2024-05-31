from django.urls import include, path

from blogs.views import templates


app_name = 'blogs'


post_urls = [
    path('', templates.PostView.as_view(), name='post'),
    path('like/', templates.LikePostView.as_view(), name='add_like'),
    path('save/', templates.SavePostView.as_view(), name='save_post'),
    path('edit/', templates.EditPostView.as_view(), name='edit_post'),
    path('delete/', templates.DeletePostView.as_view(), name='delete_post'),
    path('comment/', templates.CommentOnView.as_view(), name='add_comment'),
    path('archive/', templates.ArchivePostView.as_view(), name='archive_post'),
    path(
        route='delete-comment/<int:comment_id>/',
        view=templates.DeleteCommentView.as_view(),
        name='delete_comment',
    ),
]


posts_urls = [
    path('', templates.PostsView.as_view(), name='posts'),
    path('create/', templates.CreatePostView.as_view(), name='create_post'),
    path('<int:post_id>/', include(post_urls)),
    path(
        route='tags/<slug:tag_slug>/posts/',
        view=templates.TagPostsView.as_view(),
        name='tag_posts',
    ),
]


archive_urls = [
    path(
        route='archive/posts/',
        view=templates.PostsArchiveView.as_view(),
        name='archived_posts',
    ),
    path(
        route='archive/posts/<int:post_id>/',
        view=templates.ArchivedPostView.as_view(),
        name='archived_post',
    ),
    path(
        route='archive/posts/<int:post_id>/restore/',
        view=templates.RestorePostView.as_view(),
        name='restore_post',
    ),
    path(
        route='archive/stories/',
        view=templates.StoriesArchiveView.as_view(),
        name='archived_stories',
    ),
]


stories_urls = [
    path(
        route='create-story/',
        view=templates.CreateStoryView.as_view(),
        name='create_story',
    ),
    path(
        route='delete-story/<int:story_id>/',
        view=templates.DeleteStoryView.as_view(),
        name='delete_story',
    ),
]


urlpatterns = [
    path('posts/', include(posts_urls)),
    path('stories/', include(stories_urls)),
    path('', include(archive_urls)),
]