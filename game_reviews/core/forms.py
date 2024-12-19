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

    def upload_file(self, file, content_type, blob_name):  # Added content_type parameter
        try:
            credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
            if not credentials_path:
                raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable is not set")

            try:
                storage_client = storage.Client.from_service_account_json(credentials_path)
            except Exception as e:
                raise ValueError(f"Failed to initialize storage client: {str(e)}")

            bucket_name = os.environ.get('GS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("GS_BUCKET_NAME environment variable is not set")

            try:
                bucket = storage_client.get_bucket(bucket_name)
            except Exception as e:
                raise ValueError(f"Failed to access bucket {bucket_name}: {str(e)}")
            blob = bucket.blob(blob_name)
            content = file.read()
            try:
                blob.upload_from_string(
                    content,
                    content_type=content_type
                )
            except Exception as e:
                raise ValueError(f"Failed to upload file: {str(e)}")

            try:
                blob.make_public()
            except Exception as e:
                raise ValueError(f"Failed to make blob public: {str(e)}")

            return blob.public_url

        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            raise

    def gen_filename(self, filename):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(filename)[1].lower ()  # Convert extension to lowercase

        # Validate extension
        ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("Invalid file extension")

        return f"{timestamp}{ext}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        print(f"Saving instance with image: {instance.image}")
        # Debug
        if self.cleaned_data.get('image'):
            image_file = self.cleaned_data['image']
            dest_blob = f"{settings.GS_LOCATION}/games/images/{self.gen_filename(image_file.name)}"
            public_url = self.upload_file(image_file.file, image_file.content_type, dest_blob)
            instance.image = public_url

        if commit:
            instance.save()
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
