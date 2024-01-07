from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms


class UserCreation(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ["username", 
                  "phone", 
                  "avatar", 
                  "password1", 
                  "password2"]


class UserEdit(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "avatar",
        ]
