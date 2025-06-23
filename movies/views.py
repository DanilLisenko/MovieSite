from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Movie, Watchlist, Review, Actor, Genre , MovieCredit, SearchHistory, Person, FavoriteActor
from .forms import ReviewForm
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
import re
from django.core.cache import cache
from transliterate import translit
from django.db.models import Count, Avg
import logging
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from users.models import CustomUser
from movies.models import Review
from django.contrib import messages

def movie_list(request):
    # Получаем последние или популярные фильмы
    movies = Movie.objects.all().order_by('-rating')[:10]  # Например, 10 фильмов с наивысшим рейтингом
    context = {
        'movies': movies,
    }
    return render(request, 'movies/movie_list.html', context)

logger = logging.getLogger(__name__)

def search(request):
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '')
    sort = request.GET.get('sort', 'rating')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')
    min_rating = request.GET.get('min_rating', '')
    actor_id = request.GET.get('actor', '')

    logger.debug(f"Search params: q={query}, genre={genre}, sort={sort}, year_from={year_from}, year_to={year_to}, min_rating={min_rating}, actor_id={actor_id}")

    # Проверка пустого запроса
    if not query and not genre and not year_from and not year_to and not min_rating and not actor_id:
        return JsonResponse({'movies': [], 'actors': [], 'message': 'Запрос пустой'})

    # Кэширование
    cache_key = f"search:{query}:{genre}:{sort}:{year_from}:{year_to}:{min_rating}:{actor_id}"
    cached_results = cache.get(cache_key)
    if cached_results:
        logger.debug("Returning cached results")
        return JsonResponse(cached_results)

    movies = Movie.objects.all()
    actors = Actor.objects.all()

    # Поиск фильмов
    if query:
        if len(query) <= 2:
            movies = movies.filter(title__istartswith=query)
        else:
            try:
                search_query = SearchQuery(query, config='russian')
                movies = movies.annotate(
                    rank=SearchRank(
                        SearchVector('title', weight='A', config='russian'),
                        search_query
                    )
                ).filter(rank__gte=0.01)
            except Exception as e:
                logger.error(f"Search error: {e}")
                movies = movies.filter(title__icontains=query)

        # Поиск актеров
        if len(query) <= 2:
            actors = actors.filter(name__istartswith=query)
        else:
            try:
                search_query = SearchQuery(query, config='russian')
                actors = actors.annotate(
                    rank=SearchRank(
                        SearchVector('name', weight='A', config='russian'),
                        search_query
                    )
                ).filter(rank__gte=0.01)
            except Exception as e:
                logger.error(f"Actor search error: {e}")
                actors = actors.filter(name__icontains=query)

    # Фильтрация
    if genre:
        movies = movies.filter(genres__name=genre)
    if year_from:
        try:
            movies = movies.filter(release_date__year__gte=int(year_from))
        except ValueError:
            pass
    if year_to:
        try:
            movies = movies.filter(release_date__year__lte=int(year_to))
        except ValueError:
            pass
    if min_rating:
        try:
            movies = movies.filter(rating__gte=float(min_rating))
        except ValueError:
            pass
    if actor_id:
        try:
            movies = movies.filter(actors__id=int(actor_id))
        except ValueError:
            pass

    # Сортировка
    if sort == 'relevance' and query and len(query) > 2:
        movies = movies.order_by('-rank')
    elif sort == 'rating':
        movies = movies.order_by('-rating')
    elif sort == 'release_date':
        movies = movies.order_by('-release_date')
    else:
        movies = movies.order_by('-id')

    # Используем prefetch_related вместо select_related для genres
    movies = movies.prefetch_related('genres').only('id', 'title', 'poster_url', 'rating', 'release_date')
    actors = actors.only('id', 'name', 'photo_url')

    results = {
        'movies': [
            {
                'id': m.id,
                'title': m.title,
                'poster_url': m.poster_url or 'https://placehold.co/50x50',
                'rating': m.rating,
                'release_date': m.release_date.strftime('%Y-%m-%d') if m.release_date else ''
            }
            for m in movies
        ],
        'actors': [
            {
                'id': a.id,
                'name': a.name,
                'photo_url': a.photo_url or 'https://placehold.co/50x50'
            }
            for a in actors
        ],
    }

    logger.debug(f"Search response: {results}")
    cache.set(cache_key, results, timeout=300)
    return JsonResponse(results)

def search_actors(request):
    query = request.GET.get('q', '').strip().lower()
    if not query:
        return JsonResponse({'actors': []})

    actors = Actor.objects.filter(name__icontains=query).only('id', 'name')[:10]
    results = [
        {'id': actor.id, 'name': actor.name}
        for actor in actors
    ]
    return JsonResponse({'actors': results})

def recommend_movie(request):
    # Получаем случайный фильм
    movie = Movie.objects.order_by('?').first()  # Берем случайный фильм
    return render(request, 'movies/recommend.html', {'movie': movie})

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    recent_movies = Movie.objects.all().prefetch_related('genres')[:9]
    reviews = movie.reviews.all().order_by('-created_at')

    credits = MovieCredit.objects.filter(movie=movie).select_related('person')
    actors = movie.actors.all()
    directors = credits.filter(role='Director')
    writers = credits.filter(role='Writer')
    crew = credits.exclude(role__in=['Actor', 'Director', 'Writer'])

    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = reviews.get(user=request.user)
        except Review.DoesNotExist:
            user_review = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('users:login')
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
        form = ReviewForm(instance=user_review) if user_review else ReviewForm()

    context = {
        'movie': movie,
        'actors': actors,
        'directors': directors,
        'writers': writers,
        'crew': crew,
        'recent_movies': recent_movies,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
    }
    return render(request, 'movies/movie_detail.html', context)

def load_more_actors(request):
    """AJAX-запрос для загрузки следующей страницы актеров."""
    page = int(request.GET.get('page', 2))  # Начинаем со 2-й страницы
    actors = Actor.objects.annotate(
        movie_count=Count('movies'),
        avg_rating=Avg('movies__rating')
    ).order_by('-movie_count', '-avg_rating')

    paginator = Paginator(actors, 6)  # 6 актеров на страницу
    actors_page = paginator.get_page(page)

    actors_data = [
        {
            'id': actor.id,
            'name': actor.name,
            'photo_url': actor.photo_url or 'https://via.placeholder.com/200x300',
            'birth_date': actor.birth_date.strftime('%d.%m.%Y') if actor.birth_date else 'Дата рождения неизвестна',
            'detail_url': request.build_absolute_uri(reverse('movies:actor_detail', args=[actor.id])),
            'movie_count': actor.movie_count,
            'avg_rating': round(actor.avg_rating, 1) if actor.avg_rating else None
        }
        for actor in actors_page
    ]

    return JsonResponse({
        'actors': actors_data,
        'has_next': actors_page.has_next(),
        'next_page': actors_page.next_page_number() if actors_page.has_next() else None
    })

def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    credits = MovieCredit.objects.filter(person=person).select_related('movie')
    context = {
        'person': person,
        'credits': credits,
    }
    return render(request, 'movies/person_detail.html', context)

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
    cache_key = 'movie_collections_posters'
    posters = cache.get(cache_key)

    # Инициализация переменных
    genres = Genre.objects.all()
    years = list(range(2020, 2024))
    decades = [
        {'start_year': start, 'label': f"{start}s"}
        for start in range(2020, 1890, -10)
    ]

    if posters is None:
        base_queryset = Movie.objects.filter(
            release_date__lt='2024-01-01',
            rating__lte=9.6,
            description__isnull=False,
            poster_url__isnull=False,
            title__isnull=False
        ).exclude(
            description='',
            poster_url='',
            title=''
        ).filter(
            Q(title__regex=r'^[А-Яа-яЁё\s\d\W]+$')
        ).order_by('-rating')

        posters = {}
        used_movie_ids = []  # Список ID использованных фильмов

        # Постер для топ-100
        top_100_movie = base_queryset.exclude(id__in=used_movie_ids)[:20].first()
        if top_100_movie:
            posters['top-100'] = top_100_movie.poster_url
            used_movie_ids.append(top_100_movie.id)
        else:
            posters['top-100'] = 'https://via.placeholder.com/150?text=Топ-100'

        # Постеры для жанров
        for genre in genres:
            slug = 'genre-' + ''.join(c if c.isalnum() else '-' for c in translit(genre.name.lower(), 'ru', reversed=True)).strip('-')
            genre_movie = base_queryset.filter(genres=genre).exclude(id__in=used_movie_ids)[:20].first()
            if genre_movie:
                posters[slug] = genre_movie.poster_url
                used_movie_ids.append(genre_movie.id)
            else:
                posters[slug] = 'https://via.placeholder.com/150?text=' + genre.name

        # Постеры для годов
        for year in years:
            slug = f'year-{year}'
            year_movie = base_queryset.filter(release_date__year=year).exclude(id__in=used_movie_ids)[:20].first()
            if year_movie:
                posters[slug] = year_movie.poster_url
                used_movie_ids.append(year_movie.id)
            else:
                posters[slug] = f'https://via.placeholder.com/150?text={year}'

        # Постеры для десятилетий
        for decade in decades:
            start_year = decade['start_year']
            slug = f'decade-{start_year}'
            decade_movie = base_queryset.filter(
                release_date__year__gte=start_year,
                release_date__year__lt=start_year + 10
            ).exclude(id__in=used_movie_ids)[:20].first()
            if decade_movie:
                posters[slug] = decade_movie.poster_url
                used_movie_ids.append(decade_movie.id)
            else:
                posters[slug] = f'https://via.placeholder.com/150?text={decade["label"]}'

        # Постер для decade-2010s
        decade_2010s_movie = base_queryset.filter(
            release_date__year__gte=2010,
            release_date__year__lte=2020
        ).exclude(id__in=used_movie_ids)[:20].first()
        if decade_2010s_movie:
            posters['decade-2010s'] = decade_2010s_movie.poster_url
            used_movie_ids.append(decade_2010s_movie.id)
        else:
            posters['decade-2010s'] = 'https://via.placeholder.com/150?text=2010-2020'

        cache.set(cache_key, posters, 60 * 60)  # Кэш на 1 час

    context = {
        'genres': genres,
        'years': years,
        'decades': decades,
        'posters': posters,
    }
    return render(request, 'movies/movie_collections.html', context)

def collection_detail(request, collection_type):
    # Базовый запрос для фильмов
    base_queryset = Movie.objects.filter(
        release_date__lt='2024-01-01',
        rating__lte=9.6,
        description__isnull=False,
        poster_url__isnull=False,
        title__isnull=False
    ).exclude(
        description='',
        poster_url='',
        title=''
    ).filter(
        Q(title__regex=r'^[А-Яа-яЁё\s\d\W]+$')
    ).order_by('-rating')

    # Определение подборки
    collection_title = ""
    movies = base_queryset

    if collection_type == 'top-100':
        collection_title = "Топ-100 фильмов"
        movies = movies[:100]

    elif collection_type.startswith('genre-'):
        genre_slug = collection_type.replace('genre-', '')
        # Ищем жанр по имени в базе
        genres = Genre.objects.all()
        genre = None
        for g in genres:
            # Транслитерируем имя жанра для сравнения
            slug = ''.join(c if c.isalnum() else '-' for c in translit(g.name.lower(), 'ru', reversed=True)).strip('-')
            if slug == genre_slug:
                genre = g
                break
        if genre:
            collection_title = f"Лучшие в жанре: {genre.name}"
            movies = movies.filter(genres=genre)
        else:
            collection_title = "Жанр не найден"
            movies = Movie.objects.none()

    elif collection_type.startswith('year-'):
        try:
            year = int(collection_type.replace('year-', ''))
            collection_title = f"Лучшие фильмы {year} года"
            movies = movies.filter(release_date__year=year)
        except ValueError:
            collection_title = "Неверный год"
            movies = Movie.objects.none()

    elif collection_type == 'decade-2010s':
        collection_title = "Лучшие фильмы 2010–2020 годов"
        movies = movies.filter(release_date__year__gte=2010, release_date__year__lte=2020)

    elif collection_type.startswith('decade-'):
        try:
            decade_start = int(collection_type.replace('decade-', ''))
            collection_title = f"Лучшие фильмы {decade_start}s годов"
            movies = movies.filter(
                release_date__year__gte=decade_start,
                release_date__year__lt=decade_start + 10
            )
        except ValueError:
            collection_title = "Неверное десятилетие"
            movies = Movie.objects.none()

    context = {
        'movies': movies,
        'collection_title': collection_title,
    }
    return render(request, 'movies/movie_collection_detail.html', context)

def actor_detail(request, actor_id):
    actor = get_object_or_404(Actor, id=actor_id)
    movies = actor.movies.all()  # Получаем все фильмы, связанные с актером
    context = {
        'actor': actor,
        'movies': movies,  # Передаем фильмы в контекст
    }

    if request.user.is_authenticated:
        # Добавляем проверку наличия актера в избранном
        context['is_favorite'] = request.user.favorite_actors.filter(id=actor.id).exists()

    return render(request, 'movies/actor_detail.html', context)

def actors_list(request):
    # Получаем актёров с аннотациями
    actors = Actor.objects.annotate(
        movie_count=Count('movies'),  # Количество фильмов
        avg_rating=Avg('movies__rating')  # Средний рейтинг фильмов
    ).order_by('-movie_count', '-avg_rating')  # Сортировка по количеству фильмов, затем по рейтингу

    # Пагинация: 6 актёров на страницу
    paginator = Paginator(actors, 6)
    page_number = request.GET.get('page', 1)
    actors_page = paginator.get_page(page_number)

    return render(request, 'movies/actors_list.html', {
        'actors': actors_page,
        'total_pages': paginator.num_pages
    })

def load_more_actors(request):
    """AJAX-запрос для загрузки следующей страницы актеров."""
    page = int(request.GET.get('page', 2))  # Начинаем со 2-й страницы
    actors = Actor.objects.annotate(
        movie_count=Count('movies'),
        avg_rating=Avg('movies__rating')
    ).order_by('-movie_count', '-avg_rating')  # Та же сортировка

    paginator = Paginator(actors, 6)  # 6 актеров на страницу
    actors_page = paginator.get_page(page)

    actors_data = [
        {
            'id': actor.id,
            'name': actor.name,
            'photo_url': actor.photo_url or 'https://via.placeholder.com/200x300',
            'birth_date': actor.birth_date.strftime('%d.%m.%Y') if actor.birth_date else 'Дата рождения неизвестна',
            'detail_url': request.build_absolute_uri(reverse('movies:actor_detail', args=[actor.id])),
            'movie_count': actor.movie_count,  # Добавляем количество фильмов
            'avg_rating': actor.avg_rating,    # Добавляем средний рейтинг
        }
        for actor in actors_page
    ]

    return JsonResponse({
        'actors': actors_data,
        'has_next': actors_page.has_next(),
        'next_page': actors_page.next_page_number() if actors_page.has_next() else None
    })

def search_page(request):
    genres = Genre.objects.all()
    context = {
        'genres': genres,
    }
    return render(request, 'movies/search_page.html', context)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

@login_required
def toggle_favorite_actor(request, actor_id):
    actor = get_object_or_404(Actor, id=actor_id)
    favorite, created = FavoriteActor.objects.get_or_create(user=request.user, actor=actor)
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})

def upcoming_movies_view(request):
    upcoming_movies = Movie.objects.filter(
        release_date__gt=timezone.now().date(),
        release_date__isnull=False
    ).order_by('release_date')  # Сортировка по дате выхода
    return render(request, 'movies/upcoming.html', {'upcoming_movies': upcoming_movies})

def load_more_movie_actors(request):
    """AJAX-запрос для загрузки дополнительных актеров для конкретного фильма."""
    movie_id = request.GET.get('movie_id')
    offset = int(request.GET.get('offset', 10))  # Начинаем после первых 10 актеров
    limit = 10  # Загружаем по 10 актеров

    movie = get_object_or_404(Movie, id=movie_id)
    actors = movie.actors.all()[offset:offset + limit]

    actors_data = [
        {
            'id': actor.id,
            'name': actor.name,
            'photo_url': actor.photo_url or 'https://via.placeholder.com/150x200',
        }
        for actor in actors
    ]

    # Отладочный вывод
    print(f"Movie ID: {movie_id}, Offset: {offset}, Actors: {actors_data}")

    return JsonResponse({
        'actors': actors_data,
        'has_more': movie.actors.count() > offset + limit
    })

def is_admin(user):
    return user.is_authenticated and user.is_admin

@user_passes_test(is_admin, login_url='users:login')
def admin_dashboard(request):
    users = CustomUser.objects.all().order_by('username')
    reviews = Review.objects.all().order_by('-created_at')
    context = {
        'users': users,
        'reviews': reviews,
    }
    return render(request, 'movies/admin_dashboard.html', context)

@user_passes_test(is_admin, login_url='users:login')
def block_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user != request.user:
        user.is_blocked = True
        user.save()
        logger.info(f"Admin {request.user.username} blocked user {user.username}")
        messages.success(request, f"Пользователь {user.username} заблокирован.")
    else:
        messages.error(request, "Вы не можете заблокировать самого себя.")
    return redirect('movies:admin_dashboard')

@user_passes_test(is_admin, login_url='users:login')
def unblock_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_blocked = False
    user.save()
    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return redirect('movies:admin_dashboard')

@login_required
def delete_review(request, review_id):
    if not request.user.is_admin:
        logger.warning(f"User {request.user.username} attempted to delete review {review_id} without admin permissions")
        return JsonResponse({'error': 'У вас нет прав для удаления отзывов'}, status=403)

    review = get_object_or_404(Review, id=review_id)
    review.delete()
    logger.info(f"Admin {request.user.username} deleted review {review_id}")
    return JsonResponse({'message': 'Отзыв успешно удалён'}, status=200)

@login_required
def delete_own_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.user != request.user:
        logger.warning(f"User {request.user.username} attempted to delete review {review_id} that does not belong to them")
        messages.error(request, "Вы можете удалять только свои отзывы.")
        return redirect('movies:movie_detail', movie_id=review.movie.id)
    movie_id = review.movie.id
    review.delete()
    logger.info(f"User {request.user.username} deleted their own review {review_id}")
    messages.success(request, "Ваш отзыв успешно удалён.")
    return redirect('movies:movie_detail', movie_id=movie_id)