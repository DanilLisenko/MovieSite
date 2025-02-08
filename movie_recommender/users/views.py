from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from .forms import UserRegistrationForm, UserLoginForm
from django.shortcuts import get_object_or_404
from .forms import SaveMovieForm,EditProfileForm
from movies.models import Watchlist, Movie , Review



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('users:profile')  # Перенаправляем на профиль
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('users:profile')  # Перенаправление на профиль после входа
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    user = request.user
    watched_movies = Watchlist.objects.filter(user=user, watched=True)
    watchlist_movies = Watchlist.objects.filter(user=user, watched=False)
    # Получаем отзывы текущего пользователя (можно добавить .select_related('movie') для оптимизации)
    reviews = Review.objects.filter(user=user).select_related('movie')

    context = {
        'user': user,
        'watched_count': watched_movies.count(),
        'watchlist_count': watchlist_movies.count(),
        'watched_movies': watched_movies,
        'watchlist_movies': watchlist_movies,
        'reviews': reviews,  # Передаём отзывы в шаблон
    }
    return render(request, 'users/profile.html', context)




@login_required
def saved_movies(request):
    saved_movies = request.user.saved_movies.all()
    return render(request, 'users/saved_movies.html', {'saved_movies': saved_movies})

@login_required
def add_movie(request):
    if request.method == 'POST':
        form = SaveMovieForm(request.POST)
        if form.is_valid():
            movie = form.save(commit=False)
            movie.user = request.user
            movie.save()
            return redirect('saved_movies')
    else:
        form = SaveMovieForm()
    return render(request, 'users/add_movie.html', {'form': form})

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

