from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CustomUser
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm
from movies.models import Watchlist, Movie, Review, Genre, FavoriteActor
import logging

logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:profile')  # Redirect to profile page after successful registration
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('users:profile')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    request.user.refresh_from_db()
    user = request.user
    watched_movies = Watchlist.objects.filter(user=user, watched=True)
    watchlist_movies = Watchlist.objects.filter(user=user, watched=False)
    reviews = Review.objects.filter(user=user).select_related('movie')
    favorite_actors = FavoriteActor.objects.filter(user=user).select_related('actor')

    context = {
        'user': user,
        'watched_count': watched_movies.count(),
        'watchlist_count': watchlist_movies.count(),
        'watched_movies': watched_movies,
        'watchlist_movies': watchlist_movies,
        'reviews': reviews,
        'favorite_actors': favorite_actors,
    }
    return render(request, 'users/profile.html', context)


def user_profile(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)
    reviews = Review.objects.filter(user=profile_user).select_related('movie')
    logger.info(f"User {request.user.username or 'Anonymous'} viewed profile of {profile_user.username}")
    return render(request, 'users/user_profile.html', {
        'profile_user': profile_user,
        'reviews': reviews,
    })


@login_required
def block_user(request, user_id):
    if not request.user.is_admin:
        logger.warning(
            f"User {request.user.username} attempted to block/unblock user {user_id} without admin permissions")
        return JsonResponse({'error': 'У вас нет прав для блокировки пользователей'}, status=403)

    if request.user.id == user_id:
        logger.warning(f"User {request.user.username} attempted to block themselves")
        return JsonResponse({'error': 'Вы не можете заблокировать себя'}, status=400)

    user_to_block = get_object_or_404(CustomUser, id=user_id)
    user_to_block.is_blocked = not user_to_block.is_blocked
    user_to_block.is_active = not user_to_block.is_blocked  # Синхронизируем is_active
    user_to_block.save()
    action = 'разблокирован' if not user_to_block.is_blocked else 'заблокирован'
    logger.info(f"Admin {request.user.username} {action} user {user_to_block.username}")
    return JsonResponse({'message': f'Пользователь успешно {action}'}, status=200)


@login_required
def saved_movies(request):
    saved_movies = request.user.saved_movies.all()
    return render(request, 'users/saved_movies.html', {'saved_movies': saved_movies})


@login_required
def delete_movie(request, movie_id):
    movie_entry = get_object_or_404(Watchlist, id=movie_id, user=request.user)
    movie_entry.delete()
    return redirect('saved_movies')


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = EditProfileForm(instance=user)
    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
def watchlist_view(request):
    watchlist = Watchlist.objects.filter(user=request.user)
    return render(request, 'movies/watchlist.html', {'watchlist': watchlist})


@login_required
def add_to_watchlist(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    Watchlist.objects.get_or_create(user=request.user, movie=movie)
    return redirect('movie_detail', movie_id=movie.id)


@login_required
def mark_as_watched(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
    watchlist_item.watched = True
    watchlist_item.save()
    return redirect('movie_detail', movie_id=movie.id)


