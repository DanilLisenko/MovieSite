import asyncio
import aiohttp
from aiohttp import ClientTimeout
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from movies.models import Movie, Genre, Actor
import time

API_KEY = "8bf31002475b2fd4bc514cd9d272c4e5"
BASE_URL = "https://api.themoviedb.org/3"
MAX_CONCURRENT_REQUESTS = 30  # Лимит параллельных запросов
MAX_PAGES = 500  # TMDB позволяет до 500 страниц

class Command(BaseCommand):
    help = "Import new and upcoming movies from TMDB into the database"

    def add_arguments(self, parser):
        parser.add_argument('--pages', type=int, default=MAX_PAGES, help='Number of pages to fetch from TMDB')
        parser.add_argument('--upcoming', action='store_true', help='Fetch upcoming movies instead of popular')

    async def fetch_json(self, session, url, params=None, retries=3):
        """Асинхронный запрос к API с обработкой таймаута и повторными попытками."""
        timeout = ClientTimeout(total=30)
        for attempt in range(retries):
            try:
                async with session.get(url, params=params, timeout=timeout) as response:
                    response.raise_for_status()
                    return await response.json()
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt < retries - 1:
                    self.stdout.write(self.style.WARNING(f"Таймаут/ошибка на попытке {attempt + 1} для {url}: {str(e)}, пробую снова..."))
                    await asyncio.sleep(2)
                    continue
                else:
                    self.stdout.write(self.style.ERROR(f"Ошибка после {retries} попыток для {url}: {str(e)}"))
                    return None
        return None

    async def fetch_movies_list(self, session, pages, upcoming=False):
        """Получает список фильмов с TMDB (популярные или предстоящие)."""
        url = f"{BASE_URL}/movie/upcoming" if upcoming else f"{BASE_URL}/movie/popular"
        params = {"api_key": API_KEY, "language": "ru-RU"}
        movies = []
        existing_tmdb_ids = set(await sync_to_async(lambda: list(Movie.objects.values_list('tmdb_id', flat=True)))())

        for page in range(1, pages + 1):
            params["page"] = page
            data = await self.fetch_json(session, url, params)
            if not data or "results" not in data:
                self.stdout.write(self.style.ERROR(f"Ошибка на странице {page}: {data}"))
                break
            # Фильтруем только новые фильмы
            new_movies = [movie for movie in data["results"] if movie["id"] not in existing_tmdb_ids]
            movies.extend(new_movies)
            self.stdout.write(f"Найдено {len(new_movies)} новых фильмов на странице {page}/{pages}")
            await asyncio.sleep(0.25)  # Задержка для соблюдения лимита API

        return movies

    async def fetch_movie_details(self, session, tmdb_id, semaphore):
        """Получает детальную информацию о фильме."""
        url = f"{BASE_URL}/movie/{tmdb_id}"
        params = {"api_key": API_KEY, "language": "ru-RU", "append_to_response": "credits,videos"}
        async with semaphore:
            return await self.fetch_json(session, url, params)

    async def process_movie(self, session, movie_data, semaphore):
        """Обрабатывает и сохраняет фильм в базе данных."""
        try:
            tmdb_id = movie_data["id"]
            # Получение детальных данных
            data = await self.fetch_movie_details(session, tmdb_id, semaphore)
            if not data or "status_code" in data:
                self.stdout.write(self.style.WARNING(f"Не удалось получить данные для TMDB ID {tmdb_id}"))
                return

            title = data.get("title", "Неизвестно")
            description = data.get("overview", "")
            release_date = data.get("release_date") or None
            rating = data.get("vote_average", 0)
            poster_url = f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else ""
            # Получение трейлера
            trailer_url = ""
            videos = data.get("videos", {}).get("results", [])
            for video in videos:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                    break

            genre_names = [genre["name"] for genre in data.get("genres", [])]
            cast = data.get("credits", {}).get("cast", [])

            movie, created = await sync_to_async(Movie.objects.update_or_create)(
                tmdb_id=tmdb_id,
                defaults={
                    "title": title,
                    "description": description,
                    "release_date": release_date,
                    "rating": rating,
                    "poster_url": poster_url,
                    "trailer_url": trailer_url,
                },
            )

            action = "Добавлен" if created else "Обновлен"
            self.stdout.write(self.style.SUCCESS(f'{action} фильм: "{title}" (TMDB ID: {tmdb_id})'))

            await self.update_movie_genres(movie, genre_names)
            await self.update_movie_actors(movie, cast)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка обработки TMDB ID {tmdb_id}: {str(e)}"))

    @sync_to_async
    def update_movie_genres(self, movie, genre_names):
        """Обновляет жанры фильма."""
        genres = [Genre.objects.get_or_create(name=name)[0] for name in genre_names]
        movie.genres.set(genres)

    @sync_to_async
    def update_movie_actors(self, movie, cast):
        """Обновляет актеров фильма."""
        actors = []
        for actor_data in cast[:30]:  # Ограничим до 10 актеров для оптимизации
            actor, _ = Actor.objects.get_or_create(
                tmdb_id=actor_data["id"],
                defaults={
                    "name": actor_data["name"],
                    "photo_url": f"https://image.tmdb.org/t/p/w500{actor_data.get('profile_path')}" if actor_data.get("profile_path") else ""
                }
            )
            actors.append(actor)
        movie.actors.set(actors)

    async def load_movies(self, pages, upcoming):
        """Основной метод загрузки фильмов с TMDB."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession() as session:
            # Получаем список фильмов
            movies = await self.fetch_movies_list(session, pages, upcoming=upcoming)
            self.stdout.write(f"Всего найдено новых фильмов: {len(movies)}")

            # Обрабатываем фильмы параллельно
            tasks = [self.process_movie(session, movie_data, semaphore) for movie_data in movies]
            await asyncio.gather(*tasks)

    def handle(self, *args, **options):
        """Запускает асинхронную загрузку фильмов."""
        start_time = time.time()
        pages = min(options['pages'], MAX_PAGES)
        upcoming = options['upcoming']
        mode = "предстоящих" if upcoming else "популярных"
        self.stdout.write(f"Начинаем импорт {mode} фильмов с TMDB (страниц: {pages})...")
        asyncio.run(self.load_movies(pages, upcoming))
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Импорт завершен за {elapsed_time:.2f} секунд!"))