import requests
from movies.models import Movie, Genre
from django.core.management.base import BaseCommand
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch movies from the TMDb API and save them to the database with genres (ManyToMany)'

    def handle(self, *args, **kwargs):
        api_key = '8bf31002475b2fd4bc514cd9d272c4e5'  # Ваш API-ключ

        # Получаем справочник жанров
        genre_url = f'https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=ru-RU'
        genre_response = requests.get(genre_url)
        if genre_response.status_code == 200:
            genre_data = genre_response.json()
            # Создаём словарь {id: название}
            genre_dict = {genre['id']: genre['name'] for genre in genre_data.get('genres', [])}
        else:
            self.stdout.write(f"Ошибка получения жанров: {genre_response.status_code}")
            return

        page = 1
        while True:
            url = f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=ru-RU&page={page}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data['results']:
                    break  # Нет больше фильмов

                for item in data['results']:
                    # Обработка даты релиза
                    release_date = item.get('release_date')
                    if release_date:
                        try:
                            release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
                        except ValueError:
                            release_date = None
                    else:
                        release_date = None

                    movie, created = Movie.objects.get_or_create(
                        title=item['title'],
                        defaults={
                            'description': item.get('overview', ''),
                            'release_date': release_date,
                            'rating': item.get('vote_average', 0),
                            'poster_url': f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}",
                        }
                    )

                    # Получаем список id жанров фильма
                    genre_ids = item.get('genre_ids', [])
                    for genre_id in genre_ids:
                        genre_name = genre_dict.get(genre_id)
                        if genre_name:
                            # Получаем или создаём объект жанра
                            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                            # Добавляем жанр к фильму, если его ещё нет
                            movie.genres.add(genre_obj)

                    if created:
                        self.stdout.write(f"Добавлен фильм: {movie.title}")
                page += 1
            else:
                self.stdout.write(f"Ошибка: {response.status_code} - {response.text}")
                break
