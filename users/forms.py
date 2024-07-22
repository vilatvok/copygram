from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import Report, UserPrivacy, User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username',
            'avatar',
            'email',
            'password1',
            'password2',
        ]


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'bio',
            'gender',
        ]


class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('User is not found')
        return email


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']


class UserPrivacyForm(forms.ModelForm):
    class Meta:
        model = UserPrivacy
        exclude = ['user']
