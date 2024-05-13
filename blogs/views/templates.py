from typing import Any
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

from common.utils import create_action, get_posts, redis_client

from blogs.models import Post, Comment, PostMedia
from blogs.forms import PostForm, StoryForm
from blogs.tasks import delete_story_scheduler
from blogs.utils import like_post, save_post
from users.models import Follower



class PostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        """If user is logged then get objects except blocked users posts."""
        blocked = self.request.session.get('blocked', [])
        queryset = get_posts(blocked=blocked)
        return queryset


class TagPostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'
    slug_url_kwarg = 'tag_slug'

    def get_queryset(self):
        return (
            Post.objects.filter(tags__name__in=[self.kwargs['tag_slug']])
            .select_related('owner').prefetch_related('tags')
        )


class PostView(DetailView):
    template_name = 'blogs/post.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        blocked = self.request.session.get('blocked', [])
        queryset = get_posts(blocked=blocked)
        return queryset

    def get_context_data(self, **kwargs):
        current_user = self.request.user
        post = self.object

        context = super().get_context_data(**kwargs)
        context['files'] = post.files.all()
        context['tags'] = post.tags.all()

        # create keys in redis storage.
        check = f'post:{current_user.id}:{post.id}'
        total = f'post:{post.id}:views'

        # if key is exists - get views count.
        if redis_client.exists(check):
            context['total_views'] = int(redis_client.get(total))
        # else - increment total_views and set key ('post':'user':'post_id').
        else:
            context['total_views'] = redis_client.incr(total)
            redis_client.zincrby('post_rank', 1, post.id)
            redis_client.set(check, 1)

        owner_privacy = post.owner.privacy
        is_follower = Follower.objects.filter(
            from_user=current_user,
            to_user=post.owner,
        )
        if context['post'].is_comment:
            context['comments'] = Comment.objects.filter(
                post=post.id,
            ).select_related('owner')
        else:
            context['comments'] = None
        
        if context['comments'] != None:
            if owner_privacy.comments == 'followers':
                context['show_comments'] = is_follower
            else:
                context['show_comments'] = True

        if owner_privacy.likes == 'followers':
            context['show_likes'] = is_follower
        elif owner_privacy.likes == 'nobody':
            context['show_likes'] = False
        else:
            context['show_likes'] = True
        return context


class EditPostView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blogs/edit_post.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.model.objects.get(id=self.kwargs['post_id'])
        if request.user != post.owner:
            raise PermissionDenied('You cant edit this post')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blogs:post', args=[self.kwargs['post_id']])


class DeletePostView(DeleteView):
    model = Post
    template_name = 'blogs/post.html'
    success_url = reverse_lazy('blogs:posts')
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if request.user != post.owner:
            raise PermissionDenied('You cant delete this post')
        return super().dispatch(request, *args, **kwargs)


class StoryView(CreateView):
    form_class = StoryForm
    template_name = 'blogs/create_post.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        f.save()
        delete_story_scheduler(f.id, f.date)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])


class CreatePostView(CreateView):
    form_class = PostForm
    template_name = 'blogs/create_post.html'

    def form_valid(self, form):
        request = self.request
        images = request.FILES.getlist('files')
        if len(images) == 0:
            form.add_error(None, "At least one image is required.")
            return self.form_invalid(form)

        with transaction.atomic():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            files = []
            for img in images:
                files.append(PostMedia(post=obj, file=img))
            PostMedia.objects.bulk_create(files)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])
    

class LikePostView(View):
    def post(self, request, post_id):
        user = request.user
        post = Post.objects.get(id=post_id)
        response = like_post(user, post)
        return JsonResponse({'status': response})


class CommentOnView(View):
    def post(self, request, post_id):
        user = request.user
        post = Post.objects.get(id=post_id)
        text = request.POST.get('q')
        first_image = post.files.first()
        with transaction.atomic():
            Comment.objects.create(owner=user, post_id=post.id, text=text)
            if user != post.owner:
                create_action(user, 'commented on', post, first_image.file)
        return redirect('blogs:post', post_id)


class DeleteCommentView(View):
    def delete(self, request, post_id, comment_id):
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id)
        if comment.owner != request.user and post.owner != request.user:
            return JsonResponse({'status': 'You cant delete this method'})
        comment.delete()
        return JsonResponse({'status': 'Ok'})


class SavePostView(View):
    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        user = request.user
        response = save_post(user, post)
        return JsonResponse({'status': response})
