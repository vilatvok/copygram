from django.forms import ModelForm

from blogs.models import Post, Story


class PostForm(ModelForm):
    """Form for creating post."""
    class Meta:
        model = Post
        fields = ['description', 'tags', 'is_comment']


class StoryForm(ModelForm):
    """Form for creating story."""
    class Meta:
        model = Story
        fields = ['img']
