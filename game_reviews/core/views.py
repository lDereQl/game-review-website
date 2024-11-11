from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden
from .forms import CustomUserCreationForm
from .forms import GameForm
from .models import Game, Review


def home(request):
    latest_games = Game.objects.order_by('-id')[:10]  # Fetch the latest 10 games
    return render(request, 'core/home.html', {'latest_games': latest_games})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
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
def account_details(request):
    return render(request, 'core/account_details.html', {'user': request.user})


@login_required
def critic_dashboard(request):
    if request.user.role != 'critic':
        return redirect('home')
    return render(request, 'core/critic_dashboard.html')


def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    reviews = game.reviews.all()  # Fetch all reviews related to the game

    context = {
        'game': game,
        'reviews': reviews,
    }
    return render(request, 'core/game.html', context)


@login_required
def create_game(request):
    if not request.user.role == 'admin':  # Ensure only admins can access this view
        return HttpResponseForbidden("You are not authorized to create games.")

    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect to home after saving
    else:
        form = GameForm()

    return render(request, 'core/create_game.html', {'form': form})


@login_required
def edit_game(request, game_id):
    if not request.user.role == 'admin':  # Ensure the user is an admin
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


def game_list(request):
    games = Game.objects.all()  # Fetch all games from the database
    return render(request, 'core/game_list.html', {'games': games})
