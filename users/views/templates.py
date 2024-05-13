from django.db import models, transaction
from django.db.models.functions import Concat
from django.conf import settings
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)
from django.core.exceptions import PermissionDenied

from django_celery_beat.models import PeriodicTask

from two_factor.views.core import SetupView, LoginView
from two_factor.views.profile import DisableView
from two_factor.utils import default_device

from taggit.models import Tag

from common.utils import get_posts, redis_client

from users.forms import (
    ReportForm,
    UserEditForm,
    CustomUserCreationForm,
    CustomPasswordResetForm,
    UserPrivacyForm,
)
from users.mixins import FollowersMixin
from users.models import Block, Action, Follower, UserPrivacy
from users.utils import (
    Recommender,
    block_user,
    follow_to_user,
    send_reset_email,
    set_blocked,
)

from blogs.models import PostMedia, Story

from chats.models import PrivateChat


User = get_user_model()


class LoginUserView(LoginView):
    template_name = 'users/login.html'

    # If user has been alredy logged in, then prohibit login view.
    @method_decorator(
        user_passes_test(
            lambda u: not u.is_authenticated,
            login_url=reverse_lazy('blogs:posts'),
        )
    )
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        user = self.get_user()
        set_blocked(user, self.request)
        return super().done(form_list, **kwargs)


class SetupTwoFaView(SetupView):
    """Setup two factor authentication."""

    template_name = 'users/enable_fa.html'

    def get_success_url(self):
        return reverse_lazy('users:edit_profile')


class DisableTwoFaView(DisableView):
    """Disable two factor authentication."""

    template_name = 'users/disable_fa.html'

    def get_success_url(self):
        return reverse_lazy('users:edit_profile')


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('blogs:posts')

    def form_valid(self, form):
        request = self.request
        response = super().form_valid(form)
        user = authenticate(
            request=request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
        )
        login(request, user)
        set_blocked(user, request)
        return response


class PasswordResetView(FormView):
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('users:user_confirm')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        self.request.session['email'] = form.cleaned_data['email']
        return super().form_valid(form)


class UserConfirmView(TemplateView):
    template_name = 'users/user_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.session.get('email')
        user = User.objects.get(email=email)
        context['user_'] = user
        return context

    def post(self, request, *args, **kwargs):
        response = request.POST.get('confirm')
        if response == 'yes':
            email = request.session.pop('email')
            user = User.objects.get(email=email)
            link = 'http://127.0.0.1:8000/users/password-reset'
            send_reset_email(user, link)
            return redirect('users:password_reset_done')
        else:
            return redirect('users:password_reset')


class ProfileView(DetailView):
    """Show user profile."""

    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user'
    slug_url_kwarg = 'user_slug'

    def dispatch(self, request, *args, **kwargs):
        user = self.get_object()
        current_user = request.user
        if user != current_user:
            is_blocked = Block.objects.filter(
                models.Q(block_from=current_user, block_to=user) |
                models.Q(block_from=user, block_to=current_user),
            ).exists()
            if is_blocked:
                return redirect('users:profile', current_user.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        current_user = self.request.user

        context['posts'] = get_posts(user=user)
        context['followers'] = user.followers.count()
        context['following'] = user.following.count()

        key = f'user:{user.id}:requests'
        user_requests = redis_client.smembers(key)
        if str(current_user.id) in user_requests:
            context['request_to_follow'] = True
        else:
            context['request_to_follow'] = False

        context['is_followed'] = Follower.objects.filter(
            from_user=current_user,
            to_user=user,
        ).exists()

        # check if chat has been alredy created
        # if not, then call (create_chat) in chat app
        chat = PrivateChat.objects.filter(
            models.Q(first_user=user, second_user=current_user) |
            models.Q(first_user=current_user, second_user=user),
        ).select_related('first_user', 'second_user')

        context['is_chat'] = False
        if chat.exists():
            context['is_chat'] = chat[0]

        context['stories'] = (
            Story.objects.filter(owner=user).
            exclude(owner__in=self.request.session['blocked']).
            select_related('owner')
        )

        # recommendations for user
        recommender = Recommender()
        context['suggestions'] = recommender.suggests_for_user(user)
        return context


class EditProfileView(UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'users/edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enable'] = True if default_device(self.object) else False
        return context


class DeleteProfileView(DeleteView):
    model = User
    success_url = reverse_lazy('users:login_user')

    def get_object(self, queryset=None):
        return self.request.user


class ActivityView(ListView):
    template_name = 'users/activity.html'
    context_object_name = 'data'

    def get_queryset(self):
        user = self.request.user
        subquery = PostMedia.objects.filter(
            post=models.OuterRef('pk'),
        ).values('file')[:1]
        posts = (
            user.likes.select_related('owner').prefetch_related('tags').
            annotate(file=Concat(
                models.Value(settings.MEDIA_URL),
                models.Subquery(subquery, output_field=models.CharField()),
            ))
        )
        comments = user.comment_owner.all()
        return {'posts': posts, 'comments': comments}


class ActionsView(ListView):
    template_name = 'users/actions.html'
    context_object_name = 'actions'

    def get_queryset(self):
        user = self.request.user
        actions = Action.objects.filter(
            models.Q(post__owner=user) | models.Q(user=user),
        ).select_related('owner', 'content_type')
        redis_client.delete(f'user:{user.id}:unread_actions')
        return actions


class SavedPostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        user = self.request.user
        subquery = PostMedia.objects.filter(
            post=models.OuterRef('pk'),
        ).values('file')[:1]
        posts = (
            user.saved.select_related('owner').prefetch_related('tags').
            annotate(file=Concat(
                models.Value(settings.MEDIA_URL),
                models.Subquery(subquery, output_field=models.CharField())
            ))
        )
        return posts


class FollowersView(FollowersMixin):
    template_name = 'users/followers.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            following__to_user__slug=self.kwargs['user_slug'],
        )
        return queryset


class FollowingView(FollowersMixin):
    template_name = 'users/following.html'

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            followers__from_user__slug=self.kwargs['user_slug'],
        )
        return queryset


class BlockedView(ListView):
    """Blocked users."""

    template_name = 'users/blocked.html'
    context_object_name = 'users'

    def get_queryset(self):
        queryset = User.objects.filter(
            blocked_by__block_from=self.request.user,
        )
        return queryset


class SearchView(ListView):
    """Search users or posts (by description) in search field."""

    template_name = 'users/search.html'
    context_object_name = 'data'

    def get_queryset(self):
        request = self.request
        q = request.GET.get('q')
        query = SearchQuery(q)
        search_vector = SearchVector('username', 'email')
        is_followed = Follower.objects.filter(
            from_user=request.user,
            to_user=models.OuterRef('pk'),
        )
        users_queryset = (
            User.objects.exclude(id__in=request.session['blocked']).
            annotate(
                search=search_vector,
                rank=SearchRank(search_vector, query),
                followers_count=models.Count('followers'),
                is_followed=models.Exists(is_followed),
            ).filter(search=query).order_by("-rank")
        )

        query = SearchQuery(q)
        search_vector = SearchVector('name')
        tags_queryset = Tag.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, query),
        ).filter(search=query).order_by("-rank")

        return {'users': users_queryset, 'tags': tags_queryset}


class DeleteStoryView(DeleteView):
    model = Story
    pk_url_kwarg = 'story_id'

    def dispatch(self, request, *args, **kwargs):
        story = self.get_object()
        if request.user != story.owner:
            raise PermissionDenied('You cant delete this story')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        PeriodicTask.objects.get(
            name=f'delete-story-{self.object.id}'
        ).delete()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])


class CreateReportView(CreateView):
    form_class = ReportForm
    template_name = 'users/create_report.html'
    slug_url_kwarg = 'user_slug'
    
    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.kwargs['user_slug']])
    
    def form_valid(self, form):
        user = User.objects.get(slug=self.kwargs['user_slug'])
        f = form.save(commit=False)
        f.report_from = self.request.user
        f.report_on = user
        return super().form_valid(form)


class FollowToUserView(View):
    """
    Is used for following another user.
    Creates recommendations, base on user's followers.
    If the user has been already followed to another user then
    cancel this following and delete user's followers from recommendations.
    """

    def post(self, request, user_slug):
        from_user = request.user
        to_user = User.objects.get(slug=user_slug)
        response = follow_to_user(from_user, to_user)
        return JsonResponse({'status': response})
    

class BlockUserView(View):
    """
    Block the user and delete all connections between users.
    Otherwise, unblock the user.
    """

    def post(self, request, user_slug):
        user = request.user
        to_user = User.objects.get(slug=user_slug)
        block_user(request, user, to_user)
        return redirect('users:profile', user_slug)


class ClearActionsView(View):
    def post(self, request):
        user = request.user
        Action.objects.filter(
            models.Q(post__owner=user) | models.Q(user=user),
        ).delete()
        return redirect('users:actions')


class DeleteActionView(View):
    def delete(self, request, action_id):
        user = request.user
        action = Action.objects.get(id=action_id)
        error_response = JsonResponse({'status': "You can't delete"})
        ok_response = JsonResponse({'status': 'Ok'})
        try:
            check_action = action.target.owner
        except AttributeError:
            check_action = action.target
            if user != check_action:
                return error_response
            action.delete()
            return ok_response
        else:
            if user != check_action:
                return error_response
            action.delete()
            return ok_response


class AcceptFollowerView(View):
    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        with transaction.atomic():
            Follower.objects.create(from_user=from_user, to_user=to_user)
            Action.objects.filter(
                owner=from_user,
                user=to_user,
                act='wants to follow to you',
            ).delete()
        redis_client.srem(f'user:{to_user.id}:requests', from_user.id)
        return redirect('users:actions')
    

class RejectFollowerView(View):
    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        Action.objects.filter(
            owner=from_user,
            user=to_user,
            act='wants to follow to you',
        ).delete()
        redis_client.srem(f'user:{to_user.id}:requests', from_user.id)
        return redirect('users:actions')


class SettingsView(UpdateView):
    model = UserPrivacy
    form_class = UserPrivacyForm
    template_name = 'users/settings.html'

    def get_object(self, queryset=None):
        return UserPrivacy.objects.get(user_id=self.request.user.id)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])
