"""
URL configuration for copygram project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from two_factor.urls import urlpatterns as tf_urls

from copygram.yasg import urlpatterns as doc
from users.views import api
from blogs.views.api import PostViewSet, StoryViewSet, TagViewSet
from chats.views.api import RoomChatViewSet, PrivateChatViewSet


r = DefaultRouter()
r.register(r'tags', TagViewSet, 'tag')
r.register(r'users', api.UserViewSet, 'user')
r.register(r'saved-posts', api.SavedPostsViewSet, 'saved-post')
r.register(r'actions', api.ActionViewSet, 'action')
r.register(r'activity', api.ActivityViewSet, 'activity')
r.register(r'blocked', api.BlockedUsersViewSet, 'blocked')
r.register(r'recommendations', api.RecommendationViewSet, 'recommendation')
r.register(r'posts', PostViewSet, 'post')
r.register(r'rooms', RoomChatViewSet, 'room')
r.register(r'chats', PrivateChatViewSet, 'chat')
r.register(r'stories', StoryViewSet, 'story')


urlpatterns = [
    path('', include('users.urls')),
    path('', include('chats.urls')),
    path('admin/', admin.site.urls),
    path('posts/', include('blogs.urls')),
    path('api/', include(r.urls)),

    path('auth/', include('rest_framework.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('two/', include(tf_urls)),
]

urlpatterns += doc

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
