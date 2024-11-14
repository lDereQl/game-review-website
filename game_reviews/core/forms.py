from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Game, Comment

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')

class CustomUserEditForm(forms.ModelForm):  # Add this form for editing critic profiles
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'image', 'description', 'publication']

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'description', 'release_date', 'developer', 'genre', 'image_url', 'steam_app_id']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
