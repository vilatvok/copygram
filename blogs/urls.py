from django.urls import include, path

from blogs.views import posts, archive, stories


app_name = 'blogs'


post_urls = [
    path('', posts.PostView.as_view(), name='post'),
    path('like/', posts.LikePostView.as_view(), name='add_like'),
    path('save/', posts.SavePostView.as_view(), name='save_post'),
    path('edit/', posts.EditPostView.as_view(), name='edit_post'),
    path('delete/', posts.DeletePostView.as_view(), name='delete_post'),
    path('comment/', posts.CommentOnView.as_view(), name='add_comment'),
    path(
        route='delete-comment/<int:comment_id>/',
        view=posts.DeleteCommentView.as_view(),
        name='delete_comment',
    ),
    path('archive/', archive.ArchivePostView.as_view(), name='archive_post'),
]


posts_urls = [
    path('', posts.PostsView.as_view(), name='posts'),
    path('create/', posts.CreatePostView.as_view(), name='create_post'),
    path('<int:post_id>/', include(post_urls)),
    path(
        route='tags/<slug:tag_slug>/posts/',
        view=posts.TagPostsView.as_view(),
        name='tag_posts',
    ),
]


archive_urls = [
    path(
        route='posts/',
        view=archive.ArchivedPostsView.as_view(),
        name='archived_posts',
    ),
    path(
        route='posts/<int:post_id>/',
        view=archive.ArchivedPostView.as_view(),
        name='archived_post',
    ),
    path(
        route='posts/<int:post_id>/restore/',
        view=archive.RestorePostView.as_view(),
        name='restore_post',
    ),
    path(
        route='stories/',
        view=archive.ArchivedStoriesView.as_view(),
        name='archived_stories',
    ),
]


stories_urls = [
    path(
        route='create-story/',
        view=stories.CreateStoryView.as_view(),
        name='create_story',
    ),
    path(
        route='delete-story/<int:story_id>/',
        view=stories.DeleteStoryView.as_view(),
        name='delete_story',
    ),
]


urlpatterns = [
    path('posts/', include(posts_urls)),
    path('stories/', include(stories_urls)),
    path('archive/', include(archive_urls)),
]