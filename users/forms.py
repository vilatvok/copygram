from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class UserCreation(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 
            'avatar', 
            'password1', 
            'password2'
        ]


class UserEdit(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'bio',
            'private_account',
            'gender'
        ]