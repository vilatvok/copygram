import redis

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import PermissionDenied
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from taggit.models import Tag

from two_factor.views.core import SetupView, LoginView
from two_factor.views.profile import DisableView
from two_factor.utils import default_device

from common.utils import get_posts, create_action

from users.forms import UserCreation, UserEdit
from users.models import Block, Action, Follower
from users.utils import Recommender, set_blocked

from mainsite.models import PostMedia, Story, Comment

from chat.models import PrivateChat


User = get_user_model()


class LoginUserView(LoginView):
    template_name = 'users/login.html'

    # If user has been alredy logged in, then prohibit login view.
    @method_decorator(
        user_passes_test(
            lambda u: not u.is_authenticated, login_url=reverse_lazy('mainsite:posts')
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
        return reverse_lazy('users:edit_profile', args=[self.request.user.id])


class DisableTwoFaView(DisableView):
    """Disable two factor authentication."""

    template_name = 'users/disable_fa.html'

    def get_success_url(self):
        return reverse_lazy('users:edit_profile', args=[self.request.user.id])


class RegisterView(CreateView):
    form_class = UserCreation
    template_name = 'users/register.html'
    success_url = reverse_lazy('mainsite:posts')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = authenticate(
            self.request, 
            username=form.cleaned_data['username'], 
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        return response
    

class ProfileView(DetailView):
    """Show user profile."""
    
    template_name = 'users/profile.html'
    context_object_name = 'user'
    pk_url_kwarg = 'user_slug'

    def get_object(self, queryset=None):
        user_slug = self.kwargs['user_slug']
        user = User.objects.get(slug=user_slug)

        is_blocked = Block.objects.filter(
            Q(block_from=self.request.user, block_to=user) | 
            Q(block_from=user, block_to=self.request.user)
        ).exists()
        if is_blocked:
            raise Http404('You blocked(by) this user')
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        context['posts'] = get_posts(user)
        context['followers'] = user.user_to.all().count()
        context['following'] = user.user_from.all().count()
        context['is_followed'] = Follower.objects.filter(
            user_from=self.request.user, user_to=user
        ).exists()

        # check if chat has been alredy created
        # if not, then call (create_chat) in chat app
        chat = PrivateChat.objects.filter(
            Q(first_user=user, second_user=self.request.user) |
            Q(first_user=self.request.user, second_user=user)
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
    form_class = UserEdit
    template_name = 'users/edit_profile.html'
    pk_url_kwarg = 'user_slug'

    def get_object(self, queryset=None):
        user = User.objects.get(slug=self.kwargs['user_slug'])
        if self.request.user != user:
            raise PermissionDenied('You cant edit this profile')
        return user

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enable'] = True if default_device(self.object) else False 
        return context


class ActivityView(ListView):
    template_name = 'users/activity.html'
    context_object_name = 'data'

    def get_queryset(self):
        user = User.objects.get(id=self.request.user.id)
        subquery = PostMedia.objects.filter(
            post=OuterRef('pk')
        ).values('file')[:1]
        posts_queryset = (
            user.like.annotate(file=Subquery(subquery)).
            select_related('owner').prefetch_related('tags')
        )
        comments_queryset = user.comment_owner.all()
        return {'posts': posts_queryset, 'comments': comments_queryset}


class ActionsView(ListView):
    template_name = 'users/actions.html'
    context_object_name = 'actions'

    def get_queryset(self):
        actions = Action.objects.filter(
            Q(post__owner=self.request.user) |
            Q(user=self.request.user)
        ).select_related('owner', 'content_type')
        actions.update(unread=False)
        return actions
    

class FollowersView(ListView):
    """User's followers."""

    template_name = 'users/followers.html'
    context_object_name = 'users'
    pk_url_kwarg = 'user_slug'

    def get_queryset(self):
        is_followed = Follower.objects.filter(
            user_from=self.request.user,
            user_to=OuterRef('pk'),
        )
        queryset = (
            User.objects.exclude(id__in=self.request.session['blocked']).
            annotate(
                followers_count=Count('user_to', distinct=True), 
                is_followed=Exists(is_followed)
            ).filter(user_from__user_to__slug=self.kwargs['user_slug'])
        )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = User.objects.get(slug=self.kwargs['user_slug'])
        return context


class FollowingView(FollowersView):
    """Users I follow."""

    template_name = 'users/following.html'

    def get_queryset(self):
        is_followed = Follower.objects.filter(
            user_from=self.request.user,
            user_to=OuterRef('pk')
        )
        queryset = (
            User.objects.exclude(id__in=self.request.session['blocked']).
            annotate(
                followers_count=Count('user_to', distinct=True), 
                is_followed=Exists(is_followed)
            ).filter(user_to__user_from__slug=self.kwargs['user_slug'])
        )
        return queryset
    

class BlockedView(ListView):
    """Blocked users by user."""

    template_name = 'users/blocked.html'
    context_object_name = 'users'
    pk_url_kwarg = 'user_slug'

    def get_queryset(self):
        return User.objects.filter(
            block_to__block_from__slug=self.kwargs['user_slug']
        )


class SearchView(ListView):
    """Search users or posts (by description) in search field."""

    template_name = 'users/search.html'
    context_object_name = 'data'

    def get_queryset(self):
        q = self.request.GET.get('q')

        query = SearchQuery(q)
        search_vector = SearchVector('username', 'email')
        is_followed = Follower.objects.filter(
            user_from=self.request.user,
            user_to=OuterRef('pk')
        )
        users_queryset = (
            User.objects.exclude(id__in=self.request.session['blocked']).
            annotate(
                search=search_vector,
                rank=SearchRank(search_vector, query),
                followers_count=Count('user_to'), 
                is_followed=Exists(is_followed)
            ).filter(search=query).order_by("-rank")
        )

        query = SearchQuery(q)
        search_vector = SearchVector('name')
        tags_queryset = Tag.objects.annotate(
            search=search_vector, 
            rank=SearchRank(search_vector, query)
        ).filter(search=query).order_by("-rank")
        
        return {'users': users_queryset, 'tags': tags_queryset}


class DeleteStoryView(DeleteView):
    template_name = 'users/profile.html'
    
    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.kwargs['user_slug']])

    def get_object(self, queryset=None):
        queryset = Story.objects.get(id=self.kwargs['story_id'])
        if self.request.user != queryset.owner:
            raise PermissionDenied('You cant delete this post')
        return queryset


@require_POST
def follow(request, user_slug):
    """
    Is used for following another user.
    Creates recommendations, base on user's followers.
    If the user has been already followed another user then
    cancel this following and delete user's followers from recommendations.
    """
    user = request.user
    user_to = User.objects.get(slug=user_slug)

    is_followed = Follower.objects.filter(user_from=user, user_to=user_to)
    others = User.objects.exclude(id=user.id).filter(user_to__user_from=user_to)
    r = Recommender()

    if is_followed.exists():
        is_followed.delete()
        r.add_suggestions(user, [user_to])
        r.remove_suggestions(user, others)
        return JsonResponse({'status': 'Unfollow'})
    else:
        Follower.objects.create(user_from=user, user_to=user_to)
        r.add_suggestions(user, others)
        r.remove_suggestions(user, [user_to])
        user_following = User.objects.filter(user_to__user_from=user)
        user_followers = User.objects.filter(user_from__user_to=user)
        for _ in user_followers:
            r.add_suggestions(_, user_following)
        create_action(user, 'following you', target=user_to)
        return JsonResponse({'status': 'Follow'})


@require_POST
def block(request, user_slug):
    """
    Block the user and delete all connections between users.
    Otherwise, unblock the user.
    """
    user = request.user
    user_to = User.objects.get(slug=user_slug)
    is_blocked = Block.objects.filter(block_from=user, block_to=user_to)

    if is_blocked.exists():
        is_blocked.delete()
        set_blocked(user, request)
    else:
        Block.objects.create(block_from=user, block_to=user_to)
        posts = user.like.filter(owner=user_to)
        user_posts = user_to.like.filter(owner=user)
        for post in posts:
            post.is_like.remove(user)
            post.save()
        for post in user_posts:
            post.is_like.remove(user_to)
            post.save()
        Comment.objects.filter(
            Q(owner=user_to, post__owner=user) |
            Q(owner=user, post__owner=user_to)
        ).delete()
        Follower.objects.filter(
            Q(user_from=user_to, user_to=user) | 
            Q(user_from=user, user_to=user_to)
        ).delete()
        Action.objects.filter(
            Q(owner=user_to, post__owner=user) |
            Q(owner=user_to, user=user) |
            Q(owner=user, post__owner=user_to) |
            Q(owner=user, user=user_to)
        ).delete()
        set_blocked(user, request)
    return redirect('users:profile', user_slug)


@require_http_methods(['DELETE'])
def delete_action(request, action_id):
    action = Action.objects.get(id=action_id)
    user = request.user
    try:
        check_action = action.target.owner
    except AttributeError:
        check_action = action.target
        if user != check_action:
            return JsonResponse({'status': "You can't delete"})
        action.delete()
        return JsonResponse({'status': 'Ok'})
    else:
        if user != check_action:
            return JsonResponse({'status': "You can't delete"})
        action.delete()
        return JsonResponse({'status': 'Ok'})
