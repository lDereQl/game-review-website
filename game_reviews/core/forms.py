import os
from datetime import datetime

from django import forms
from google.cloud import storage
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.text import slugify

from .models import CustomUser, Game, Comment, Review


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')


class CustomUserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'image', 'description', 'publication', 'role']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'image': forms.URLInput(attrs={'placeholder': 'Profile Image URL'}),
        }


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'password')


class GameForm(forms.ModelForm):

    def upload_file(self, file, content_type, blob_name):
        try:
            # Initialize storage client
            storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)
            bucket = storage_client.get_bucket(settings.GS_BUCKET_NAME)
            blob = bucket.blob(blob_name)

            # Read and upload the file content
            content = file.read()
            blob.upload_from_string(content, content_type=content_type)

            # Make the file publicly accessible
            blob.make_public()
            return blob.public_url
        except Exception as e:
            raise ValueError(f"Error uploading file: {e}")

    def gen_filename(self, filename):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(filename)[1].lower()

        # Validate file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if ext not in allowed_extensions:
            raise ValueError("Invalid file extension")

        return f"{timestamp}{ext}"

    def save(self, commit=True):
        instance = super().save(commit=False)  # Create an instance without saving to the database
        try:
            # Check if a new image is uploaded
            if 'image' in self.cleaned_data:
                image_file = self.cleaned_data['image']
                # Only handle new image uploads
                if hasattr(image_file, 'content_type'):  # Check if it's a new file
                    dest_blob = f"{settings.GS_LOCATION}/games/images/{self.gen_filename(image_file.name)}"
                    public_url = self.upload_file(image_file, image_file.content_type, dest_blob)
                    instance.image = public_url  # Update with the new uploaded image URL

            # Handle video and file fields similarly (if needed)
            if 'video' in self.cleaned_data:
                video_file = self.cleaned_data['video']
                if hasattr(video_file, 'content_type'):
                    dest_blob = f"{settings.GS_LOCATION}/games/videos/{self.gen_filename(video_file.name)}"
                    public_url = self.upload_file(video_file, video_file.content_type, dest_blob)
                    instance.video = public_url

            if 'file' in self.cleaned_data:
                file_file = self.cleaned_data['file']
                if hasattr(file_file, 'content_type'):
                    dest_blob = f"{settings.GS_LOCATION}/games/files/{self.gen_filename(file_file.name)}"
                    public_url = self.upload_file(file_file, file_file.content_type, dest_blob)
                    instance.file = public_url

            # Save the instance
            if commit:
                instance.save()

        except Exception as e:
            print(f"ERROR: {e}")
            raise ValueError(f"Failed to save game: {e}")

        return instance

    class Meta:
        model = Game
        fields = [
            'title', 'description', 'release_date', 'developer', 'publisher',
            'genre', 'image', 'video', 'file', 'steam_app_id', 'parent_game',
            'age_rating', 'platform', 'category', 'tags'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            'tags': forms.SelectMultiple(),
            'category': forms.SelectMultiple(),
            'platform': forms.SelectMultiple(),
            'genre': forms.Textarea(attrs={'rows': 2, 'maxlength': '255'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment', 'parent']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
            'parent': forms.HiddenInput(),  # Hide parent field if adding a reply
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        labels = {
            'rating': 'Your Rating',
            'comment': 'Review Comment',
            'title': 'Review Title',
        }
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),  # Rating from 1 to 5
            'comment': forms.Textarea(attrs={'rows': 4}),
            'title': forms.TextInput(attrs={'placeholder': 'Review Title'}),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if not comment or len(comment) < 10:
            raise forms.ValidationError("The comment must be at least 10 characters long.")
        return comment

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("The title cannot be empty.")
        return title


class RoleChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role']

    ROLE_CHOICES = [
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('critic', 'Critic'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)


class FileUploadForm(forms.Form):
    file = forms.FileField(label="Choose a File")
