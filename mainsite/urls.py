from django.urls import path

from . import views


app_name = "mainsite"

urlpatterns = [
    path("", views.Posts.as_view(), name="posts"),
    path("post/<int:post_id>/", views.Post_.as_view(), name="post"),
    path("likes/<int:post_id>/", views.likes, name="like"),
    path("create/", views.CreatePost.as_view(), name="create"),
    path("tag/<int:tag_id>/", views.Tags.as_view(), name="tags"),
    path("edit/<int:post_id>/", views.EditPost.as_view(), name="edit"),
    path("delete/<int:post_id>/", views.DeletePost.as_view(), name="delete"),
    path("add_comment/<int:post_id>/", views.comment, name="add_comment"),
    path("create_story/", views.Stories.as_view(), name="create_story"),
    path("most_viewed/", views.post_ranked, name="most_viewed")
]
