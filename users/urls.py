from django.urls import path, reverse_lazy, include
from django.contrib.auth.views import LogoutView, PasswordChangeView

from users.views import templates


app_name = 'users'

urlpatterns = [
    path('login/', templates.LoginUserView.as_view(), name='login_user'),
    path('logout/', LogoutView.as_view(), name='logout_user'),
    path('register/', templates.RegisterView.as_view(), name='register'),
    path('<slug:user_slug>/', 
        include(
            [
                path('profile/', templates.ProfileView.as_view(), name='profile'),
                path('activity/', templates.ActivityView.as_view(), name='activity'),
                path('edit_profile/', templates.EditProfileView.as_view(), name='edit_profile'),
                path('followers/', templates.FollowersView.as_view(), name='followers'),
                path('following/', templates.FollowingView.as_view(), name='following'),
                path('blocked/', templates.BlockedView.as_view(), name='blocked'),
                path('block/', templates.block, name='block'),
                path('follow/', templates.follow, name='follow'),
                path(
                    'delete_story/<int:story_id>/', 
                    templates.DeleteStoryView.as_view(), 
                    name='delete_story'
                ),
            ]         
        ),
    ),
    path('change_password/',
        PasswordChangeView.as_view(
            success_url=reverse_lazy('mainsite:posts'),
            template_name='users/change_password.html',
        ),
        name='change_password',
    ),  
    path('two_fa/', templates.SetupTwoFaView.as_view(), name='enable_fa'),
    path('disable_two_fa/', templates.DisableTwoFaView.as_view(), name='disable_fa'),
    path('actions/', templates.ActionsView.as_view(), name='actions'),
    path('delete_action/<int:action_id>/', templates.delete_action, name='delete_action'),
    path('search/', templates.SearchView.as_view(), name='search'),
]
