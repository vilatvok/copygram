from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)

from taggit.models import Tag

from common.utils import get_blocked_users, redis_client

from users.forms import ReportForm
from users.models import User, Action, Follower

from blogs.models import Post


class ActionsView(ListView):
    template_name = 'users/actions.html'
    context_object_name = 'actions'

    def get_queryset(self):
        user = self.request.user
        actions = Action.objects.filter(
            models.Q(post__owner=user) | 
            models.Q(user=user),
        ).select_related('owner', 'content_type')
        redis_client.delete(f'user:{user.id}:unread_actions')
        return actions


class ClearActionsView(View):
    def post(self, request):
        user = request.user
        Action.objects.filter(
            models.Q(post__owner=user) |
            models.Q(user=user),
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


class ActivityView(ListView):
    template_name = 'users/activity.html'
    context_object_name = 'data'

    def get_queryset(self):
        user = self.request.user
        posts = (
            Post.objects.annotated().
            exclude(archived=True).filter(likes=user)
        )
        comments = (
            user.comments.exclude(post__archived=True).
            select_related('post', 'owner')
        )
        return {'posts': posts, 'comments': comments}


class SavedPostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        user = self.request.user
        posts = (
            Post.objects.annotated().
            exclude(archived=True).filter(saved=user)
        )
        return posts


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
        blocked_users = get_blocked_users(request.user)
        users_queryset = (
            User.objects.exclude(id__in=blocked_users).
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
