from django.urls import include, path

from mainsite.views import templates


app_name = 'mainsite'

urlpatterns = [
    path('posts/', templates.PostsView.as_view(), name='posts'),
    path('create/', templates.create_post, name='create'),
    path('post/<int:post_id>/', templates.PostView.as_view(), name='post'),
    path('post/<int:post_id>/',
        include(
            [
                path('like/', templates.add_like, name='add_like'),
                path('edit/', templates.EditPostView.as_view(), name='edit'),
                path('delete/', templates.DeletePostView.as_view(), name='delete'),
                path('add_comment/', templates.add_comment, name='add_comment'),
                path(
                    'delete_comment/<int:comment_id>/', 
                     templates.delete_comment, 
                     name='delete_comment'
                ),
            ]
        ),
    ),
    path(
        'tag/<slug:tag_slug>/posts/', 
         templates.TagPostsView.as_view(), 
         name='tag_posts'
    ),
    path('create_story/', templates.StoriesView.as_view(), name='create_story'),
]