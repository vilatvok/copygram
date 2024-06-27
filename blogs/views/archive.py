from django.shortcuts import redirect
from django.views import View
from django.views.generic.list import ListView

from blogs import utils
from blogs.models import Post
from blogs.views.posts import PostView


class ArchivedPostsView(ListView):
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
        obj.archived = True
        obj.save()
        return redirect('users:profile', self.request.user.slug)


class RestorePostView(View):
    def post(self, request, post_id):
        obj = Post.objects.get(id=post_id)
        obj.archived = False
        obj.save()
        return redirect('blogs:archived_posts')


class ArchivedStoriesView(ListView):
    template_name = 'blogs/stories_archive.html'
    context_object_name = 'stories'
    
    def get_queryset(self):
        return utils.get_archived_stories(self.request.user)
