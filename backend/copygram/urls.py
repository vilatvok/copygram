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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from two_factor.urls import urlpatterns as tf_urls

from users.api import views as users_api
from blogs.api import views as blogs_api
from chats.api import views as chats_api


r = DefaultRouter()
r.register(r'tags', blogs_api.TagViewSet, 'tag')
r.register(r'users', users_api.UserViewSet, 'user')
r.register(r'referrals', users_api.ReferralViewSet, 'referral')
r.register(r'posts', blogs_api.PostViewSet, 'post')
r.register(r'stories', blogs_api.StoryViewSet, 'story')
r.register(r'uninteresting', blogs_api.UninterestingPostViewSet, 'uninteresting')
r.register(r'groups', chats_api.GroupChatViewSet, 'group')
r.register(r'chats', chats_api.PrivateChatViewSet, 'chat')
r.register(r'actions', users_api.ActionViewSet, 'action')
r.register(r'archive', blogs_api.ArchiveViewSet, 'archive')
r.register(r'activity', users_api.ActivityViewSet, 'activity')
r.register(r'blocked', users_api.BlockedUsersViewSet, 'blocked')
r.register(r'saved-posts', users_api.SavedPostsViewSet, 'saved-post')
r.register(r'recommendations', users_api.RecommendationViewSet, 'recommendation')
r.register(r'activities', users_api.UserActivityViewSet, 'user-activity')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('rest_framework.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('two-factor/', include(tf_urls)),

    path('api/', include(r.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        route='api/docs/',
        view=SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('api/social-auth/', include('drf_social_oauth2.urls', namespace='drf')),
    path('', include('users.urls', namespace='users')),
    path('', include('chats.urls', namespace='chats')),
    path('', include('blogs.urls', namespace='blogs')),
]


if settings.DEBUG:
    urlpatterns += static(
        prefix=settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
