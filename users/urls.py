from django.urls import path, reverse_lazy, include
from django.contrib.auth.views import (
    LogoutView,
    PasswordChangeView,
    PasswordResetDoneView,
    PasswordResetConfirmView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.api import views
from users.views import accounts, actions, followers, auth


app_name = 'users'


user_urls = [
    path('', accounts.ProfileView.as_view(), name='profile'),
    path('followers/', followers.FollowersView.as_view(), name='followers'),
    path('following/', followers.FollowingView.as_view(), name='following'),
    path('follow/', followers.FollowToUserView.as_view(), name='follow'),
    path('block/', accounts.BlockUserView.as_view(), name='block'),
    path('report/', actions.CreateReportView.as_view(), name='create_report'),
]


password_urls = [
    # Templates
    path(
        route='change-password/',
        view=PasswordChangeView.as_view(
            success_url=reverse_lazy('blogs:posts'),
            template_name='users/change_password.html',
        ),
        name='change_password',
    ),
    path(
        route='password-reset/',
        view=auth.PasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        route='password-user-confirm/',
        view=auth.PasswordUserConfirmView.as_view(),
        name='password_user_confirm',
    ),
    path(
        route='password-reset/done/',
        view=PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name='password_reset_done',
    ),
    path(
        route='password-reset/<uidb64>/<token>/',
        view=PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy('users:login'),
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
    path('api/password-change/', views.PasswordChangeAPIView.as_view()),
    path('api/settings/', views.SettingsAPIView.as_view()),
    path('api/password-reset/', views.PasswordResetAPIView.as_view()),
    path(
        route='api/password-reset-confirm/<uidb64>/<token>/',
        view=views.PasswordResetConfirmAPIView.as_view(),
    ),
]


urlpatterns = [
    path('login/', auth.LoginUserView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', auth.RegisterView.as_view(), name='register'),
    path(
        route='api/register-confirm/<uidb64>/<token>/',
        view=views.RegisterConfirmAPIView.as_view(),
    ),
    path(
        route='register-confirm/<uidb64>/<token>/',
        view=auth.RegisterConfirmView.as_view(),
        name='register_confirm',
    ),
    path(
        route='register-admin/',
        view=auth.AdminRegisterView.as_view(),
        name='admin_register',
    ),
    path('actions/', actions.ActionsView.as_view(), name='actions'),
    path(
        route='clear-actions/',
        view=actions.ClearActionsView.as_view(),
        name='clear_actions',
    ),
    path('activity/', actions.ActivityView.as_view(), name='activity'),
    path(
        route='saved-posts/',
        view=actions.SavedPostsView.as_view(),
        name='saved_posts',
    ),
    path('blocked/', accounts.BlockedView.as_view(), name='blocked'),
    path('search/', actions.SearchView.as_view(), name='search'),
    path('settings/', accounts.SettingsView.as_view(), name='settings'),
    path(
        route='accept-follower/<slug:user_slug>/',
        view=followers.AcceptFollowerView.as_view(),
        name='accept_follower',
    ),
    path(
        route='reject-follower/<slug:user_slug>/',
        view=followers.RejectFollowerView.as_view(),
        name='reject_follower',
    ),
    path(
        route='api/accept-follower/<slug:user_slug>/',
        view=views.AcceptFollowerAPIView.as_view(),
    ),
    path(
        route='api/reject-follower/<slug:user_slug>/',
        view=views.RejectFollowerAPIView.as_view(),
    ),
    path('api/vip-status/', views.VipAPIView.as_view()),
    path(
        route='users/edit/',
        view=accounts.EditProfileView.as_view(),
        name='edit_profile',
    ),
    path(
        route='delete-account/',
        view=accounts.DeleteProfileView.as_view(),
        name='delete_account',
    ),
    path('users/<slug:user_slug>/', include(user_urls)),
    path(
        route='delete-action/<int:action_id>/',
        view=actions.DeleteActionView.as_view(),
        name='delete_action',
    ),
    
    path('two_fa/', auth.SetupTwoFaView.as_view(), name='enable_fa'),
    path(
        route='disable-two-fa/',
        view=auth.DisableTwoFaView.as_view(),
        name='disable_fa',
    ),
] + password_urls