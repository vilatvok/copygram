import redis

from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import *

from .models import Post, Comment
from .forms import PostForm, EditPostForm, StoryForm

from users.utils import create_action, get_res


r = redis.Redis(host="redis", port=6379, db=0)


# Create your views here.
class Posts(ListView):
    template_name = "mainsite/posts.html"
    context_object_name = "posts"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            blockf = self.request.user.block_from.all().values_list("block_to", flat=True)
            blockt = self.request.user.block_to.all().values_list("block_from", flat=True)
            return (
                Post.objects.exclude(owner__in=set(list(blockf) + list(blockt)))
                .select_related("owner")
                .prefetch_related("tags")
            )
        return Post.objects.all().select_related("owner").prefetch_related("tags")
        

class Post_(DetailView):
    model = Post
    template_name = "mainsite/post.html"
    context_object_name = "post"
    pk_url_kwarg = "post_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        check = f"post:{self.request.user.username}:{self.kwargs['post_id']}"
        total = f"post:{self.kwargs['post_id']}:views"
        if r.exists(check):
            context["total_views"] = int(r.get(total))
        else:
            context["total_views"] = r.incr(total)
            r.zincrby("post_rank", 1, self.kwargs["post_id"])
            r.set(check, 1)

        context["likes"] = context["post"].total_likes
        if context["post"].is_comment:
            context["no_comment"] = True
            context["comments"] = Comment.objects.filter(post=self.kwargs["post_id"])
        else:
            context["no_comment"] = False
        return context


class CreatePost(CreateView):
    form_class = PostForm
    template_name = "mainsite/create_post.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        create_action(self.request.user, "created post", f.photo)
        get_res(self.request)
        # send_notification.delay()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("users:profile", args=[self.request.user.id])


class EditPost(UpdateView):
    form_class = EditPostForm
    template_name = "mainsite/edit_post.html"
    pk_url_kwarg = "post_id"

    def get_success_url(self):
        return reverse_lazy("users:profile", args=[self.request.user.id])


class DeletePost(DeleteView):
    template_name = "mainsite/post.html"
    success_url = reverse_lazy("mainsite:posts")
    pk_url_kwarg = "post_id"

    def get_object(self, queryset=None):
        p = Post.objects.get(id=self.kwargs["post_id"])
        self.photo = p.photo
        return p

    def form_valid(self, form):
        get_res(self.request)
        return super().form_valid(form)


class Tags(Posts):
    def get_queryset(self):
        return Post.objects.filter(tags__id=self.kwargs["tag_id"])


class Stories(CreateView):
    form_class = StoryForm
    template_name = "mainsite/create_post.html"

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        create_action(self.request.user, "public story", f.img)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("users:profile", args=[self.request.user.id])


###############################################################################
# Function view


def comment(request, post_id):
    q = request.GET.get("q")
    Comment.objects.create(owner=request.user, post_id=post_id, text=q)
    return redirect("mainsite:post", post_id)


def likes(request, post_id):
    post = Post.objects.get(id=post_id)
    if post.is_like.filter(id=request.user.id).exists():
        post.is_like.remove(request.user)
    else:
        post.is_like.add(request.user)
        create_action(request.user, "liked post", post.photo, post.owner)
    post.save()
    return redirect("mainsite:post", post_id)


def post_ranked(request):
    post_ranking = r.zrange("post_rank", 0, -1, desc=True, withscores=True)

    ids, scores = zip(*[(int(id), int(score)) for id, score in post_ranking])

    most_viewed = Post.objects.filter(id__in=ids)

    over = zip(most_viewed, scores)

    return render(request, "mainsite/view_rate.html", {"most_viewed": over})
