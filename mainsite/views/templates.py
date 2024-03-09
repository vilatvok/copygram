import redis

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

from mainsite.models import Post, Comment, PostMedia
from mainsite.forms import PostForm, StoryForm
from mainsite.tasks import delete_story_scheduler

from common.utils import create_action, get_posts


# Connect redis
r = redis.Redis(host='redis', port=6379, db=0)


class PostsView(ListView):
    template_name = 'mainsite/posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        """If user is logged then get objects except blocked users posts."""
        queryset = get_posts(blocked=self.request.session.get('blocked', []))
        return queryset
    
        
class PostView(DetailView):
    queryset = Post.objects.all().select_related('owner').prefetch_related('tags')
    template_name = 'mainsite/post.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['files'] = self.object.files.all()
        context['tags'] = self.object.tags.all()
        
        # create keys in redis storage.
        check = f'post:{self.request.user.username}:{self.kwargs["post_id"]}'
        total = f'post:{self.kwargs["post_id"]}:views'

        # if key is exists - get views count.
        if r.exists(check):
            context['total_views'] = int(r.get(total))
        # else - increment total_views and set key ('post':'user':'post_id').
        else:
            context['total_views'] = r.incr(total)
            r.zincrby('post_rank', 1, self.kwargs['post_id'])
            r.set(check, 1)

        if context['post'].is_comment:
            context['comments'] = (
                Comment.objects.filter(post=self.kwargs['post_id']).
                select_related('owner')
            )
        else:
            context['comments'] = None
        return context
    

class TagPostsView(ListView):
    template_name = 'mainsite/posts.html'
    context_object_name = 'posts'
    slug_url_kwarg = 'tag_slug'

    def get_queryset(self):
        return (
            Post.objects.filter(tags__name__in=[self.kwargs['tag_slug']]).
            select_related('owner').prefetch_related('tags')
        )


class EditPostView(UpdateView):
    form_class = PostForm
    template_name = 'mainsite/edit_post.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = Post.objects.get(id=self.kwargs['post_id'])
        if self.request.user != post.owner:
            raise PermissionDenied('You cant edit this post')
        return post

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])


class DeletePostView(DeleteView):
    template_name = 'mainsite/post.html'
    success_url = reverse_lazy('mainsite:posts')
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = Post.objects.get(id=self.kwargs['post_id'])
        if self.request.user != post.owner:
            raise PermissionDenied('You cant delete this post')
        return post


class StoriesView(CreateView):
    form_class = StoryForm
    template_name = 'mainsite/create_post.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        f.save()
        delete_story_scheduler(f.id, f.date)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('users:profile', args=[self.request.user.slug])
      
       
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            for media in request.FILES.getlist('files'):
                PostMedia.objects.create(file=media, post=obj)
            return redirect('users:profile', request.user.slug)
    else:
        form = PostForm()
    return render(request, 'mainsite/create_post.html', {'form': form})


@require_POST
def add_comment(request, post_id):
    q = request.POST.get('q')
    post = Post.objects.get(id=post_id)
    file = post.files.first()
    user = request.user
    Comment.objects.create(owner=request.user, post_id=post_id, text=q)
    if user != post.owner:
        create_action(request.user, 'comment on', file.file, post)
    return redirect('mainsite:post', post_id)


@require_http_methods(['DELETE'])
def delete_comment(request, post_id, comment_id):
    post = Post.objects.get(id=post_id)
    comment = Comment.objects.get(id=comment_id)
    if comment.owner != request.user and post.owner != request.user:
        return JsonResponse({'status': 'You cant delete this method'})
    comment.delete()
    return JsonResponse({'status': 'Ok'})
    

@require_POST
def add_like(request, post_id):
    post = Post.objects.get(id=post_id)
    file = post.files.first()
    user = request.user
   
    if post.is_like.filter(id=user.id).exists():
        post.is_like.remove(user)
        post.save()
        return JsonResponse({'status': 'Unlike'})
    # if post has been already liked, then unlike post.
    else:
        post.is_like.add(user)
        if user != post.owner:
            create_action(user, 'liked post', file.file, post)
        post.save()
        return JsonResponse({'status': 'Like'})