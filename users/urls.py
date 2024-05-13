from django.urls import path, reverse_lazy, include
from django.contrib.auth import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import templates, api


app_name = 'users'


user_urls = [
    path('', templates.ProfileView.as_view(), name='profile'),
    path('followers/', templates.FollowersView.as_view(), name='followers'),
    path('following/', templates.FollowingView.as_view(), name='following'),
    path('block/', templates.BlockUserView.as_view(), name='block'),
    path('follow/', templates.FollowToUserView.as_view(), name='follow'),
    path('report/', templates.CreateReportView.as_view(), name='create_report'),
]


password_urls = [
    # Templates
    path(
        route='change-password/',
        view=views.PasswordChangeView.as_view(
            success_url=reverse_lazy('blogs:posts'),
            template_name='users/change_password.html',
        ),
        name='change_password',
    ),
    path(
        route='password-reset/',
        view=templates.PasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        route='password-user-confirm/',
        view=templates.UserConfirmView.as_view(),
        name='user_confirm',
    ),
    path(
        route='password-reset/done/',
        view=views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name='password_reset_done',
    ),
    path(
        route='password-reset/<uidb64>/<token>/',
        view=views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy('users:login_user'),
        ),
        name='password_reset_confirm',
    ),

    # API
    path(
        route='api/token/',
        view=TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        route='api/token/refresh/',
        view=TokenRefreshView.as_view(),
        name='token_refresh',
        ),
    path('api/password-change/', api.PasswordChangeAPIView.as_view()),
    path('api/settings/', api.SettingsAPIView.as_view()),
    path('api/password-reset/', api.PasswordResetAPIView.as_view()),
    path(
        route='api/password-reset-confirm/<uidb64>/<token>/',
        view=api.PasswordResetConfirmAPIView.as_view(),
    ),
]


urlpatterns = [
    path('login/', templates.LoginUserView.as_view(), name='login_user'),
    path('logout/', views.LogoutView.as_view(), name='logout_user'),
    path('register/', templates.RegisterView.as_view(), name='register'),
    path('actions/', templates.ActionsView.as_view(), name='actions'),
    path('clear-actions/', templates.ClearActionsView.as_view(), name='clear_actions'),
    path('activity/', templates.ActivityView.as_view(), name='activity'),
    path(
        route='saved-posts/',
        view=templates.SavedPostsView.as_view(),
        name='saved_posts',
    ),
    path('blocked/', templates.BlockedView.as_view(), name='blocked'),
    path('search/', templates.SearchView.as_view(), name='search'),
    path('settings/', templates.SettingsView.as_view(), name='settings'),
    path(
        route='accept-follower/<slug:user_slug>/',
        view=templates.AcceptFollowerView.as_view(),
        name='accept_follower',
    ),
    path(
        route='reject-follower/<slug:user_slug>/',
        view=templates.RejectFollowerView.as_view(),
        name='reject_follower',
    ),
    path(
        route='api/accept-follower/<slug:user_slug>/',
        view=api.AcceptFollowerAPIView.as_view(),
    ),
    path(
        route='api/reject-follower/<slug:user_slug>/',
        view=api.RejectFollowerAPIView.as_view(),
    ),
    path(
        route='users/edit/',
        view=templates.EditProfileView.as_view(),
        name='edit_profile',
    ),
    path(
        route='delete-account/',
        view=templates.DeleteProfileView.as_view(),
        name='delete_account',
    ),
    path('users/<slug:user_slug>/', include(user_urls)),
    path(
        route='delete-story/<int:story_id>/',
        view=templates.DeleteStoryView.as_view(),
        name='delete_story',
    ),
    path(
        route='delete-action/<int:action_id>/',
        view=templates.DeleteActionView.as_view(),
        name='delete_action',
    ),
    
    path('two_fa/', templates.SetupTwoFaView.as_view(), name='enable_fa'),
    path(
        route='disable-two-fa/',
        view=templates.DisableTwoFaView.as_view(),
        name='disable_fa',
    ),
] + password_urls