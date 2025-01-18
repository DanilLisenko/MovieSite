from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from movies.models import Movie
from datetime import timedelta
from django.utils import timezone


def home(request):
    # Получаем текущую дату
    today = timezone.now().date()  # Только дата, без времени
    # Вычисляем дату 30 дней назад
    thirty_days_ago = today - timedelta(days=30)

    # Фильтруем фильмы
    recent_movies = Movie.objects.filter(
        release_date__gte=thirty_days_ago,
        release_date__lte=today,  # Исключаем фильмы с датой в будущем
        title__regex=r'^[a-zA-Zа-яА-Я0-9\s\-\.,:;!?\'"()]+$'  # Допустимые символы
    ).order_by('-rating', '-release_date')  # Сначала рейтинг, потом дата выхода

    return render(request, 'base.html', {'recent_movies': recent_movies})


urlpatterns = [
    path('admin/', admin.site.urls),  # Админка Django
    path('users/', include('users.urls')),  # Маршруты приложения пользователей
    path('movies/', include(('movies.urls', 'movies'), namespace='movies')),
    path('', home, name='home'),  # Главная страница
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

