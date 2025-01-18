import requests
from movies.models import Movie
from django.core.management.base import BaseCommand
from datetime import datetime


from django.core.management.base import BaseCommand
import requests
from datetime import datetime
from movies.models import Movie

class Command(BaseCommand):
    help = 'Fetch movies from the TMDb API and save them to the database'

    def handle(self, *args, **kwargs):
        api_key = '8bf31002475b2fd4bc514cd9d272c4e5'  # Вставьте ваш API-ключ
        page = 1
        while True:
            url = f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=ru-RU&page={page}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data['results']:
                    break  # Прекращаем, если фильмов больше нет на следующей странице
                for item in data['results']:
                    # Проверка и установка корректной даты релиза
                    release_date = item.get('release_date')
                    if release_date:
                        try:
                            release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
                        except ValueError:
                            release_date = None  # Если формат даты некорректен, ставим None
                    else:
                        release_date = None  # Если даты нет, ставим None

                    movie, created = Movie.objects.get_or_create(
                        title=item['title'],
                        defaults={
                            'description': item.get('overview', ''),
                            'genre': 'Unknown',  # Вы можете настроить сопоставление жанров
                            'release_date': release_date,
                            'rating': item.get('vote_average', 0),
                            'poster_url': f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}",
                        }
                    )
                    if created:
                        print(f"Добавлен фильм: {movie.title}")
                page += 1  # Переходим к следующей странице
            else:
                print(f"Ошибка: {response.status_code} - {response.text}")
                break
