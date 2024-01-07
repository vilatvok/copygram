from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import *
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test

from .forms import UserCreation, UserEdit
from .models import *
from .utils import create_action, Recommender
from .tasks import check_story

from mainsite.models import Story, Post

from two_factor.views.core import SetupView, LoginView
from two_factor.views.profile import DisableView


# Create your views here.


class LoginView(LoginView):
    template_name = "users/login.html"

    @method_decorator(
        user_passes_test(
            lambda u: not u.is_authenticated, login_url=reverse_lazy("mainsite:posts")
        )
    )
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SetupTwoFa(SetupView):
    template_name = "users/enable_fa.html"

    def get_success_url(self):
        return reverse_lazy("users:edit_profile", args=[self.request.user.id])


class DisableTwoFa(DisableView):
    template_name = "users/disable_fa.html"

    def get_success_url(self):
        return reverse_lazy("users:edit_profile", args=[self.request.user.id])


class Register(CreateView):
    form_class = UserCreation
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login_user")


class Profile(DetailView):
    model = get_user_model()
    template_name = "users/profile.html"
    context_object_name = "user"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = (
            Post.objects.filter(owner=self.kwargs["pk"])
            .select_related("owner")
            .prefetch_related("tags")
        )
        context["followers"] = self.object.user_to.all()
        context["following"] = self.object.user_from.all()
        context["blocked"] = Block.objects.filter(
            Q(block_from=self.request.user, block_to=self.object)
            | Q(block_from=self.object, block_to=self.request.user)
        )

        r = Recommender()
        context["suggestions"] = r.suggests_for_user(self.object)

        if Story.objects.filter(owner=self.object).exists():
            check_story.delay()

        context["stories"] = Story.objects.filter(owner=self.kwargs["pk"])
        return context


class EditProfile(UpdateView):
    model = get_user_model()
    form_class = UserEdit
    template_name = "users/edit_profile.html"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse_lazy("users:profile", args=[self.request.user.id])


class Act(ListView):
    template_name = "users/actions.html"
    context_object_name = "actions"

    def get_queryset(self):
        blockf = self.request.user.block_from.all().values_list("block_to", flat=True)
        blockt = self.request.user.block_to.all().values_list("block_from", flat=True)
        tc = ContentType.objects.get_for_model(self.request.user)
        return (
            Action.objects.filter(tc=tc, ti=self.request.user.id)
            .exclude(owner__in=set(list(blockf) + list(blockt)))
            .select_related("owner")
            .prefetch_related("target")
        )


class DeleteAct(DeleteView):
    model = Action
    template_name = "users/actions.html"
    success_url = reverse_lazy("users:actions")
    pk_url_kwarg = "act_id"


class ShowFollowers(ListView):
    template_name = "users/followers.html"
    context_object_name = "users"
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        blockf = self.request.user.block_from.all().values_list("block_to", flat=True)
        blockt = self.request.user.block_to.all().values_list("block_from", flat=True)
        return (
            get_user_model()
            .objects.filter(user_from__user_to=self.kwargs["user_id"])
            .exclude(id__in=set(list(blockf) + list(blockt)))
        )


class ShowFollowing(ShowFollowers):
    def get_queryset(self):
        return get_user_model().objects.filter(
            user_to__user_from=self.kwargs["user_id"]
        )


class ShowBlocked(ListView):
    template_name = "users/blocked.html"
    context_object_name = "users"
    pk_url_kwarg = "user_id"

    def get_queryset(self):
        return get_user_model().objects.filter(
            block_to__block_from=self.kwargs["user_id"]
        )


class Search(ListView):
    template_name = "users/followers.html"
    context_object_name = "users"

    def get_queryset(self):
        q = self.request.GET.get("q")
        if len(q) != 0:
            return get_user_model().objects.filter(username__icontains=q)
        return


def follow(request, user_id):
    user = get_user_model().objects.get(id=user_id)

    r = Recommender()
    others = list(get_user_model().objects.filter(user_from__user_to=user.id))

    check = Follower.objects.filter(user_from=request.user, user_to=user)
    if check.exists():
        r.remove_suggestions(request.user, others)
        check.delete()
        if Follower.objects.filter(user_from=request.user).exists():
            r.add_suggestions(request.user, [user])
    else:
        r.add_suggestions(request.user, others)
        r.remove_suggestions(request.user, [user])
        Follower.objects.create(user_from=request.user, user_to=user)
        create_action(request.user, "following to", user.avatar, user)

    return redirect("users:profile", user_id)


def block(request, user_id):
    user = get_user_model().objects.get(id=user_id)

    check = Block.objects.filter(block_from=request.user, block_to=user)

    if check.exists():
        check.delete()
    else:
        Block.objects.create(block_from=request.user, block_to=user)
        Follower.objects.filter(
            Q(user_from=user, user_to=request.user)
            | Q(user_from=request.user, user_to=user)
        ).delete()

    return redirect("users:profile", user_id)
