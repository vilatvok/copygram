from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType

from django_celery_beat.models import PeriodicTask

from common.utils import create_action, redis_client

from blogs import utils
from blogs.models import Post, Comment, PostMedia, Story
from blogs.forms import PostForm, StoryForm

from users.models import Archive, Follower


class PostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        """If user is logged then get objects except blocked users posts."""
        queryset = utils.get_posts(self.request.user)
        return queryset


class TagPostsView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'
    slug_url_kwarg = 'tag_slug'

    def get_queryset(self):
        qs = (
            Post.objects.annotated().exclude(archived=True).
            filter(tags__name__in=[self.kwargs['tag_slug']])
        )
        return qs


class PostView(DetailView):
    template_name = 'blogs/post.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        queryset = utils.get_posts(self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        current_user = self.request.user
        post = self.object

        context = super().get_context_data(**kwargs)
        context['files'] = post.get_files()
        context['tags'] = post.get_tags()

        # create keys in redis storage
        check = f'post:{current_user.id}:{post.id}'
        total = f'post:{post.id}:views'

        # if key is exists - get views count
        if redis_client.exists(check):
            context['total_views'] = int(redis_client.get(total))
        # else - increment total_views and set key ('post':'user':'post_id')
        else:
            context['total_views'] = redis_client.incr(total)
            redis_client.zincrby('post_rank', 1, post.id)
            redis_client.set(check, 1)

        owner_privacy = post.owner.privacy
        is_follower = Follower.objects.filter(
            from_user=current_user,
            to_user=post.owner,
        )

        if post.is_comment:
            comments = (
                post.comments.with_tree_fields().with_likes().
                select_related('owner', 'post', 'parent')
            )
            context['comments'] = comments
        else:
            context['comments'] = None
        if current_user != post.owner:
            # check if user hid likes count
            if post.is_comment:
                if owner_privacy.comments == 'followers':
                    context['show_comments'] = is_follower.exists()
                else:
                    context['show_comments'] = True

            # check if user hid likes count
            if owner_privacy.likes == 'followers':
                context['show_likes'] = is_follower.exists()
            elif owner_privacy.likes == 'nobody':
                context['show_likes'] = False
            else:
                context['show_likes'] = True
        else:
            if post.is_comment:
                context['show_comments'] = True
            context['show_likes'] = True
        return context


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


class EditPostView(UpdateView):
    queryset = Post.objects.select_related('owner')
    form_class = PostForm
    template_name = 'blogs/edit_post.html'
    pk_url_kwarg = 'post_id'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user != self.object.owner:
            raise PermissionDenied('You cant edit this post')
        return response

    def get_success_url(self):
        return reverse_lazy('blogs:post', args=[self.kwargs['post_id']])


class DeletePostView(DeleteView):
    model = Post
    template_name = 'blogs/post.html'
    success_url = reverse_lazy('blogs:posts')
    pk_url_kwarg = 'post_id'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user != self.object.owner:
            raise PermissionDenied('You cant delete this post')
        return response


class PostsArchiveView(ListView):
    template_name = 'blogs/posts.html'
    context_object_name = 'posts'
    extra_context = {'url': 'archived'}

    def get_queryset(self):
        return utils.get_archived_posts(self.request.user)


class ArchivedPostView(PostView):
    template_name = 'blogs/archived_post.html'

    def get_queryset(self):
        queryset = utils.get_archived_posts(self.request.user)
        return queryset


class ArchivePostView(View):
    def post(self, request, post_id):
        obj = Post.objects.get(id=post_id)
        target_ct = ContentType.objects.get_for_model(obj)
        obj.archived = True
        with transaction.atomic():
            obj.save()
            Archive.objects.create(content_type=target_ct, object_id=obj.id)
        return redirect('users:profile', self.request.user.slug)


class RestorePostView(View):
    def post(self, request, post_id):
        obj = Post.objects.get(id=post_id)
        obj.archived = False
        with transaction.atomic():
            obj.save()
            Archive.objects.get(post=obj).delete()
        return redirect('blogs:archived_posts')


class StoriesArchiveView(ListView):
    template_name = 'blogs/stories_archive.html'
    context_object_name = 'stories'
    
    def get_queryset(self):
        return utils.get_archived_stories(self.request.user)


class SavePostView(View):
    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        user = request.user
        response = utils.save_post(user, post)
        return JsonResponse({'status': response})


class LikePostView(View):
    def post(self, request, post_id):
        user = request.user
        post = utils.get_posts(user).get(pk=post_id)
        response = utils.like_post(user, post)
        return JsonResponse({'status': response})


class CommentOnView(View):
    def post(self, request, post_id):
        user = request.user
        post = utils.get_posts(user).get(pk=post_id)
        text = request.POST.get('q')
        with transaction.atomic():
            Comment.objects.create(owner=user, post_id=post.id, text=text)
            if user != post.owner:
                create_action(user, 'commented on', post, post.file)
        return redirect('blogs:post', post_id)


class DeleteCommentView(View):
    def delete(self, request, post_id, comment_id):
        post = Post.objects.get(id=post_id)
        comment = Comment.objects.get(id=comment_id)
        if comment.owner != request.user and post.owner != request.user:
            return JsonResponse({'status': 'You cant delete this comment'})
        comment.delete()
        return JsonResponse({'status': 'Ok'})


class CreateStoryView(CreateView):
    form_class = StoryForm
    template_name = 'blogs/create_story.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        f.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])


class DeleteStoryView(DeleteView):
    model = Story
    pk_url_kwarg = 'story_id'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user != self.object.owner:
            raise PermissionDenied('You cant delete this post')
        return response

    def form_valid(self, form):
        with transaction.atomic():
            task_name = f'archive-story-{self.object.id}'
            self.object.delete()
            task = PeriodicTask.objects.get(name=task_name)
            task.delete()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])
