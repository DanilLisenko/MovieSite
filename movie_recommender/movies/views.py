from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Movie, Watchlist, Review  # Импортируем Review
from .forms import ReviewForm

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
    movie = get_object_or_404(Movie, id=movie_id)
    recent_movies = Movie.objects.all().prefetch_related('genres')[:9]
    # Получаем все отзывы для фильма (отсортированные по дате)
    reviews = movie.reviews.all().order_by('-created_at')

    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = reviews.get(user=request.user)
        except Review.DoesNotExist:
            user_review = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('users:login')
        # Если отзыв уже существует, обновляем его; иначе — создаём новый
        if user_review:
            form = ReviewForm(request.POST, instance=user_review)
        else:
            form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()
            return redirect('movies:movie_detail', movie_id=movie.id)
    else:
        # Если пользователь уже оставил отзыв, заполняем форму его данными
        if user_review:
            form = ReviewForm(instance=user_review)
        else:
            form = ReviewForm()

    context = {
        'movie': movie,
        'recent_movies': recent_movies,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
    }
    return render(request, 'movie_detail.html', context)

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