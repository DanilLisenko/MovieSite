from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from movies.models import Movie, Genre
from datetime import timedelta
from django.utils import timezone


def home(request):
    # Получаем текущую дату
    today = timezone.now().date()
    # Вычисляем дату 60 дней назад
    sixty_days_ago = today - timedelta(days=60)

    # Получаем 50 недавних фильмов
    recent_movies = Movie.objects.filter(
        release_date__gte=sixty_days_ago,
        release_date__lte=today,
        rating__lt=9.5,
        title__regex=r'^[a-zA-Zа-яА-Я0-9\s\-\.,:;!?\'"()]+$'
    ).order_by('-rating', '-release_date')[:50]

    # Получаем случайный постер из топ-100 фильмов
    top_100_movie = Movie.objects.filter(
        rating__gte=8.0  # Предполагаем, что топ-100 — это фильмы с рейтингом 8.0 и выше
    ).order_by('?').first()  # Случайный выбор
    hero_poster_url = top_100_movie.poster_url if top_100_movie and top_100_movie.poster_url else 'https://via.placeholder.com/800x400'

    # Получаем все жанры
    genres = Genre.objects.all()

    return render(request, 'base.html', {
        'recent_movies': recent_movies,
        'genres': genres,
        'hero_poster_url': hero_poster_url
    })

handler404 = 'movies.views.custom_404'
handler500 = 'movies.views.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),  # Админка Django
    path('users/', include('users.urls')),  # Маршруты приложения пользователей
    path('movies/', include(('movies.urls', 'movies'), namespace='movies')),
    path('', home, name='home'),  # Главная страница
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)