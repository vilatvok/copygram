from django import forms
from django.contrib.auth import get_user_model

from chats.models import RoomChat


class RoomForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        self.fields['users'].queryset = queryset

    class Meta:
        model = RoomChat
        fields = ['image', 'name', 'users']


class EditRoomForm(RoomForm):
    add_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        queryset2 = kwargs.pop('queryset2', None)
        super().__init__(*args, **kwargs)
        self.fields['add_users'].queryset = queryset2

    class Meta:
        model = RoomChat
        fields = ['image', 'name', 'users', 'add_users']
