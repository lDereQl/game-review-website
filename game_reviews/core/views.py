from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from .forms import CustomUserCreationForm, GameForm, CustomUserEditForm, CommentForm, ReviewForm, RoleChangeForm, \
    FileUploadForm
from .models import Game, Review, Comment, CustomUser, Like
from .utils import get_game_info, upload_to_storage
import requests
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import upload_image_to_storage, verify_id_image


def home(request):
    latest_games = Game.objects.order_by('-id')[:10]  # Fetch the latest 10 games
    return render(request, 'core/home.html', {'latest_games': latest_games})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user without committing to the database yet
            user = form.save(commit=False)

            # Assign 'admin' role if this is the first user (id=1), otherwise 'user' role
            if CustomUser.objects.count() == 0:
                user.role = 'admin'  # Assign 'admin' to the first user
            else:
                user.role = 'user'  # Assign 'user' to all other users

            user.save()  # Now save the user to the database

            # Authenticate and log in the user
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def account_details(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    is_critic = user.role == 'critic'

    # Check if the logged-in user is an admin
    if request.user.role == 'admin':
        if request.method == 'POST':
            form = RoleChangeForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, f'User role has been updated to {user.role}.')
                return redirect('account_details', user_id=user.id)
        else:
            form = RoleChangeForm(instance=user)

        context = {
            'user': user,
            'is_critic': is_critic,
            'form': form,
        }
    else:
        context = {
            'user': user,
            'is_critic': is_critic,
        }

    return render(request, 'core/account_details.html', context)


@login_required
def critic_dashboard(request):
    if request.user.role != 'critic':
        return redirect('home')
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/critic_dashboard.html', {'reviews': reviews})


@login_required
def edit_critic(request):
    if request.user.role != 'critic':
        return HttpResponseForbidden("You are not authorized to edit this profile.")

    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account_details')
    else:
        form = CustomUserEditForm(instance=request.user)

    return render(request, 'core/edit_critic.html', {'form': form})


@login_required
def delete_critic(request):
    if request.user.role != 'critic':
        return HttpResponseForbidden("You are not authorized to delete this profile.")
    return render(request, 'core/delete_critic.html')


@login_required
def delete_critic_confirm(request):
    if request.user.role != 'critic':
        return HttpResponseForbidden("You are not authorized to delete this profile.")

    # Delete the critic's account
    request.user.delete()
    return redirect('home')  # Redirect to the homepage or another appropriate page


@login_required
def verify_critic(request):
    """
    Verifies the critic's identity using a password and uploaded work ID.
    """
    if request.user.role != 'critic':
        return HttpResponseForbidden("You are not authorized to verify this profile.")

    extracted_text = ""  # Initialize variable to hold extracted text

    if request.method == 'POST':
        try:
            # Step 1: Verify the password
            password = request.POST.get('password')
            user = authenticate(username=request.user.username, password=password)

            if user is None:
                messages.error(request, "Incorrect password. Please try again.")
                return render(request, 'core/verify_critic.html', {'extracted_text': extracted_text})

            # Step 2: Handle the file upload
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                messages.error(request, "Please upload an image of your work ID.")
                return render(request, 'core/verify_critic.html', {'extracted_text': extracted_text})

            # Save the uploaded file using the new function
            file_path = upload_image_to_storage(uploaded_file)
            print(f"File saved at: {file_path}")

            # Step 3: Run OCR-based verification
            result = verify_id_image(file_path)
            extracted_text = result['text']  # Capture extracted text for debugging
            print(f"Verification Result: {result}")

            # Step 4: Provide feedback
            if result['verified'] and result['confidence'] >= 0.8:
                messages.success(request, f"Verification successful! Confidence: {result['confidence']:.2f}")
            else:
                messages.error(request, f"Verification failed. Confidence: {result['confidence']:.2f}")
        except Exception as e:
            print(f"Error in verify_critic view: {e}")
            messages.error(request, "An unexpected error occurred. Please try again.")

    return render(request, 'core/verify_critic.html', {'extracted_text': extracted_text})


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    steam_info = get_game_info(game.steam_app_id)

    # Fetch base game or DLCs
    if game.parent_game:
        parent_game = game.parent_game
        dlcs = []
    else:
        parent_game = None
        dlcs = Game.objects.filter(parent_game=game)

    # Fetch the latest two reviews
    latest_reviews = game.reviews.order_by('-created_at')[:2]

    # User and critic check
    is_critic = request.user.is_authenticated and request.user.role == 'critic'
    user_has_reviewed = False
    user_review = None
    if is_critic:
        try:
            user_review = Review.objects.get(game=game, user=request.user)
            user_has_reviewed = True
        except Review.DoesNotExist:
            pass

    # Comments pagination (number of comments per page set by query parameter)
    comments_per_page = request.GET.get('comments_per_page', 5)  # Default to 10
    try:
        comments_per_page = int(comments_per_page)
    except ValueError:
        comments_per_page = 5

    top_level_comments = Comment.objects.filter(game=game, parent__isnull=True).select_related('user')
    paginator = Paginator(top_level_comments, comments_per_page)

    page = request.GET.get('page')
    try:
        comments = paginator.page(page)
    except PageNotAnInteger:
        comments = paginator.page(1)
    except EmptyPage:
        comments = paginator.page(paginator.num_pages)

    # Paginate replies for each comment (limit to 5 replies per page)
    paginated_replies = {}
    for comment in comments:
        replies = comment.replies.all()
        reply_paginator = Paginator(replies, 3)
        paginated_replies[comment.id] = reply_paginator.page(1)  # Show first page of replies by default

    # Comment form
    comment_form = CommentForm()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.user = request.user
            new_comment.game = game
            parent_id = request.POST.get('parent_id')
            if parent_id:
                new_comment.parent = get_object_or_404(Comment, id=parent_id)
            new_comment.save()
            return redirect('game_detail', game_id=game.id)

    context = {
        'game': game,
        'steam_info': steam_info,
        'latest_reviews': latest_reviews,
        'is_critic': is_critic,
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
        'comments': comments,  # Paginated top-level comments
        'comment_form': comment_form,
        'paginated_replies': paginated_replies,  # First page of replies for each comment
        'comments_per_page': comments_per_page,
    }
    return render(request, 'core/game.html', context)


@login_required
def create_game(request):
    if not request.user.role == 'admin':
        return HttpResponseForbidden("You are not authorized to create games.")

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)  # Include request.FILES
        if form.is_valid():
            game = form.save()  # Automatically handles uploaded files
            return redirect('home')
    else:
        form = GameForm()

    return render(request, 'core/create_game.html', {'form': form})


@login_required
def edit_game(request, game_id):
    if not (request.user.role == 'admin' or request.user.role == 'moderator'):
        return HttpResponseForbidden("You are not authorized to edit games.")

    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = GameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            return redirect('game_detail', game_id=game.id)
    else:
        form = GameForm(instance=game)

    return render(request, 'core/edit_game.html', {'form': form, 'game': game})


@login_required
def delete_game(request, game_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to delete games.")

    game = get_object_or_404(Game, id=game_id)

    if request.method == 'POST':
        game.delete()
        return redirect('home')  # Redirect to home after deletion

    return render(request, 'core/delete_game_confirm.html', {'game': game})


def game_list(request):
    games = Game.objects.all()  # Fetch all games from the database
    return render(request, 'core/game_list.html', {'games': games})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user.role == 'moderator':
        comment.delete()
        return redirect('game_detail', game_id=comment.game.id)  # Redirect to the game page
    else:
        return HttpResponseForbidden("You don't have permission to delete this comment.")


def all_reviews(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    reviews = game.reviews.order_by('-created_at')
    return render(request, 'core/all_reviews.html', {'game': game, 'reviews': reviews})


@login_required
def create_review(request, game_id):
    if request.user.role != 'critic':
        return HttpResponseForbidden("You are not authorized to create reviews.")

    game = get_object_or_404(Game, id=game_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.game = game
            review.save()
            return redirect('game_detail', game_id=game.id)
    else:
        form = ReviewForm()

    return render(request, 'core/create_review.html', {'form': form, 'game': game})


@login_required
def user_list(request):
    # Only allow users with 'admin' role to access this page
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to access this page.")

    # Optionally, you can fetch all users or perform any other logic for the admin dashboard
    users = CustomUser.objects.all()

    context = {
        'users': users,
    }

    return render(request, 'core/user_list.html', context)


@login_required
def update_user_role(request, user_id):
    if request.user.role != 'admin':
        return redirect('home')  # Redirect non-admin users

    user = get_object_or_404(CustomUser, id=user_id)

    # Check if the user is the first user (superuser)
    first_user = CustomUser.objects.order_by('id').first()
    if user.id == first_user.id:
        messages.error(request, "This user is a superuser, and their role can't be changed.")
        return redirect('user_list')  # Redirect back to the user list page

    if request.method == 'POST':
        form = RoleChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User role has been updated to {user.role}.')
            return redirect('user_list')  # Redirect back to the admin dashboard
    else:
        form = RoleChangeForm(instance=user)

    return render(request, 'core/update_user_role.html', {'form': form, 'user': user})


def upload_file(request):
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Save the file (Google Cloud Storage handles the upload automatically)
            try:
                uploaded_file.save()
                messages.success(request, "File uploaded successfully!")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            return redirect('upload_file')
    else:
        form = FileUploadForm()

    return render(request, 'upload_file.html', {'form': form})


@login_required
def edit_comment(request, comment_id):
    # Fetch the comment ensuring the current user owns it
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            # Mark the comment as edited
            comment.edited = True
            form.save()
            return redirect('game_detail', game_id=comment.game.id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'core/edit_comment.html', {'form': form, 'comment': comment})


def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    # Check if the user already liked the comment
    like, created = Like.objects.get_or_create(user=user, comment=comment)
    if not created:
        # If the like already exists, unlike it
        like.delete()
        liked = False
    else:
        liked = True

    # Return the updated like count
    like_count = comment.like_set.count()

    return JsonResponse({"liked": liked, "like_count": like_count})


@login_required
def import_steam_comments(request, game_id):
    # Ensure only admin users can trigger this function
    if not request.user.is_authenticated or request.user.role != 'admin':
        return HttpResponseForbidden("You do not have permission to import Steam comments.")

    # Fetch the game and check for steam_app_id
    game = get_object_or_404(Game, id=game_id)
    if not game.steam_app_id:
        messages.error(request, "This game does not have a Steam App ID.")
        return redirect('game_detail', game_id=game.id)

    # Ensure steam_user exists or create it
    steam_user, created = CustomUser.objects.get_or_create(
        username="steam_user",
        defaults={"password": "importpassword", "email": "steam@example.com", "role": "user"}
    )

    # Delete old Steam comments (optional cleanup)
    Comment.objects.filter(game=game, user=steam_user).delete()

    # Fetch new Steam comments
    url = f"https://store.steampowered.com/appreviews/{game.steam_app_id}?json=1&filter=recent&language=english"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        reviews = data.get("reviews", [])
        imported_count = 0

        for review in reviews:
            content = review.get("review", "")
            if content:
                Comment.objects.create(
                    comment=content,
                    user=steam_user,
                    game=game
                )
                imported_count += 1

        if imported_count > 0:
            messages.success(request, f"Successfully imported {imported_count} comments from Steam.")
        else:
            messages.info(request, "No new comments were found to import from Steam.")

    except requests.RequestException as e:
        messages.error(request, f"Failed to fetch Steam comments: {str(e)}")

    return redirect('game_detail', game_id=game.id)


@login_required
def vote_review(request, review_id, vote_type):
    review = get_object_or_404(Review, id=review_id)

    if review.has_voted(request.user):
        return HttpResponseForbidden("You have already voted on this review.")

    if vote_type == "up":
        review.helpful_votes += 1
    elif vote_type == "down":
        review.helpful_votes -= 1

    review.voters.add(request.user)
    review.save()

    return redirect("game_detail", game_id=review.game.id)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Ensure the user is authorized to edit this review
    if request.user.role != 'critic' or review.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this review.")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('game_detail', game_id=review.game.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'core/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Ensure only moderators can delete reviews
    if request.user.role != 'moderator':
        return HttpResponseForbidden("You are not authorized to delete this review.")

    if request.method == "POST":
        review.delete()
        return redirect('game_detail', game_id=review.game.id)

    return render(request, 'core/delete_review_confirm.html', {'review': review})



@login_required
def ban_user(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to ban users.")

    user = get_object_or_404(CustomUser, id=user_id)

    # Prevent banning other admins
    if user.role == 'admin':
        messages.error(request, "You cannot ban an admin.")
        return redirect('user_list')

    user.banned = True
    user.save()
    messages.success(request, f"{user.username} has been banned successfully.")
    return redirect('user_list')
