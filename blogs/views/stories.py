from django.db import transaction
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, DeleteView

from django_celery_beat.models import PeriodicTask

from blogs.models import Story
from blogs.forms import StoryForm


class CreateStoryView(CreateView):
    form_class = StoryForm
    template_name = 'blogs/create_story.html'

    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        f.save()
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        return user.get_absolute_url()


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
            try:
                task = PeriodicTask.objects.get(name=task_name)
                task.delete()
            except ObjectDoesNotExist:
                pass
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        user = self.request.user
        return user.get_absolute_url()
