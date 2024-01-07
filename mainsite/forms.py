from django import forms
from .models import Post, Story


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["photo", "description", "tags"]


class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["description", "tags"]


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["img"]
