from django.shortcuts import render
from django.http import JsonResponse
from .models import Movie,Watchlist
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.signals import post_save
from django.dispatch import receiver


def recommend_movie(request):
    # Получаем случайный фильм
    movie = Movie.objects.order_by('?').first()  # Берем случайный фильм
    return render(request, 'movies/recommend.html', {'movie': movie})


def search_movie_tmdb(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query')  # Получаем название фильма
        url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={search_query}&language=ru-RU"
        response = requests.get(url)
        data = response.json()
        movies = data.get('results', [])
        return render(request, 'movies/search_results.html', {'movies': movies})

    return render(request, 'movies/search_movie_tmdb.html')

def movie_detail(request, movie_id):
    # Получаем фильм по его ID или возвращаем 404
    movie = get_object_or_404(Movie, id=movie_id)
    # Получаем список недавних фильмов с предзагрузкой жанров
    recent_movies = Movie.objects.all().prefetch_related('genres')[:9]
    # Передаём их в контекст шаблона
    return render(request, 'movie_detail.html', {
        'movie': movie,
        'recent_movies': recent_movies,
    })
@login_required
def add_to_watchlist(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    # Проверяем, есть ли фильм уже в списке
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
    if created:
        watchlist_item.watched = False  # Устанавливаем как "отложенный"
        watchlist_item.save()
    return redirect('movies:movie_detail', movie_id=movie.id)


@login_required
def mark_as_watched(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)
    watchlist_item.watched = True  # Отмечаем как просмотренный
    watchlist_item.save()
    return redirect('movies:movie_detail', movie_id=movie.id)