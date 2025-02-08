from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Movie, Watchlist, Review, Actor, Genre , MovieCredit, Person
from .forms import ReviewForm

def actors_list(request):
    actors = Person.objects.filter(
        moviecredit__role='Actor'
    ).distinct().prefetch_related('moviecredit_set')
    return render(request, 'movies/actors_list.html', {'actors': actors})

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

    actors = MovieCredit.objects.filter(movie=movie, role='Actor')[:5]
    directors = MovieCredit.objects.filter(movie=movie, role='Director')

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
        'actors': actors,
        'directors': directors,
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

def movie_collections(request):
    # Получаем топ фильмов (например, с самым высоким рейтингом) до 2020 года
    top_movies = Movie.objects.filter(release_date__lt='2020-01-01').order_by('-rating')[:100]

    # Получаем фильмы по жанрам, фильтруем по году выпуска, сортируем по рейтингу
    genres = Genre.objects.all()
    genre_collections = {
        genre.name: genre.movie_set.filter(release_date__lt='2020-01-01').order_by('-rating')[:100]
        for genre in genres
    }

    context = {
        'top_movies': top_movies,
        'genre_collections': genre_collections
    }

    return render(request, 'movies/movie_collections.html', context)



def actors_list(request):
    """Страница со списком актеров."""
    actors = Actor.objects.all()
    return render(request, 'movies/actors_list.html', {'actors': actors})


def actor_detail(request, actor_id):
    """Страница актера с его биографией и фильмами."""
    actor = get_object_or_404(Actor, id=actor_id)
    movies = actor.movies.all()  # Получаем фильмы, где снимался актер

    return render(request, 'movies/actor_detail.html', {
        'actor': actor,
        'movies': movies,
    })


def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    filmography = MovieCredit.objects.filter(person=person).select_related('movie')
    return render(request, 'movies/person_detail.html', {
        'person': person,
        'filmography': filmography
    })