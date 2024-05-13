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
    path(
        route='delete-comment/<int:comment_id>/',
        view=templates.DeleteCommentView.as_view(),
        name='delete_comment',
    ),
]


urlpatterns = [
    path('', templates.PostsView.as_view(), name='posts'),
    path('create/', templates.CreatePostView.as_view(), name='create_post'),
    path('<int:post_id>/', include(post_urls)),
    path(
        route='create-story/',
        view=templates.StoryView.as_view(),
        name='create_story',
    ),
    path(
        route='tags/<slug:tag_slug>/posts/',
        view=templates.TagPostsView.as_view(),
        name='tag_posts',
    ),
]
