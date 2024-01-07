from django.urls import path, reverse_lazy
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.urls import reverse_lazy

from . import views
from . import utils

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(template_name="users/login.html"), name="login_user"),
    path("logout/", LogoutView.as_view(), name="logout_user"),
    path("register/", views.Register.as_view(), name="register"),
    path("profile/<int:pk>/", views.Profile.as_view(), name="profile"),
    path("edit_profile/<int:pk>/", views.EditProfile.as_view(), name="edit_profile"),
    path(
        "change_password/",
        PasswordChangeView.as_view(
            success_url=reverse_lazy("mainsite:posts"),
            template_name="users/change_password.html",
        ),
        name="change_password",
    ),
    path("actions/", views.Act.as_view(), name="actions"),
    path("followers/<int:user_id>/", views.ShowFollowers.as_view(), name="followers"),
    path("following/<int:user_id>/", views.ShowFollowing.as_view(), name="following"),
    path("blocked/<int:user_id>/", views.ShowBlocked.as_view(), name="blocked"),
    path("follows/<int:user_id>/", views.follow, name="follow"),
    path("block/<int:user_id>/", views.block, name="block"),
    path("delete_act/<int:act_id>/", views.DeleteAct.as_view(), name="delete_act"),
    path("res/", utils.get_res, name="res"),
    path("two_fa/", views.SetupTwoFa.as_view(), name="enable_fa"),
    path("disable_two_fa/", views.DisableTwoFa.as_view(), name="disable_fa"),
    path("search/", views.Search.as_view(), name="search"),

]
