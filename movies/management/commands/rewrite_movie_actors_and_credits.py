# movies/management/commands/rewrite_movie_actors_and_credits.py
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from movies.models import Movie, Actor, Person, MovieCredit
import urllib.parse
import re

API_KEY = "8bf31002475b2fd4bc514cd9d272c4e5"
BASE_URL = "https://api.themoviedb.org/3"
MAX_CONCURRENT_REQUESTS = 30

class Command(BaseCommand):
    help = "Rewrite movie-actor relationships and add directors/writers using TMDB API"

    def is_valid_title(self, title):
        """Проверяет, является ли название фильма валидным (не содержит URL, спам и т.д.)."""
        url_pattern = re.compile(r'http[s]?://|www\.|\.com|\.org|\.net|\d{4}[a-zA-Z0-9]{3,}', re.IGNORECASE)
        if url_pattern.search(title):
            return False
        if not title.strip() or not re.search(r'\w', title, re.UNICODE):
            return False
        return True

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

    async def search_movie(self, session, title, release_date, semaphore):
        """Ищет фильм в TMDB по названию и году выпуска."""
        if not self.is_valid_title(title):
            self.stdout.write(self.style.WARNING(f"Пропущен фильм с некорректным названием: {title}"))
            return None

        url = f"{BASE_URL}/search/movie"
        params = {
            "api_key": API_KEY,
            "query": urllib.parse.quote(title),
            "page": 1
        }
        if release_date:
            params["year"] = release_date.year

        async with semaphore:
            # Первая попытка: поиск на русском
            params["language"] = "ru-RU"
            data = await self.fetch_json(session, url, params)
            if data and "results" in data and data["results"]:
                self.stdout.write(self.style.SUCCESS(f"Найден TMDB ID для фильма '{title}' (ru-RU): {data['results'][0]['id']}"))
                return data["results"][0]["id"]

            # Вторая попытка: поиск на английском
            params["language"] = "en-US"
            data = await self.fetch_json(session, url, params)
            if data and "results" in data and data["results"]:
                self.stdout.write(self.style.SUCCESS(f"Найден TMDB ID для фильма '{title}' (en-US): {data['results'][0]['id']}"))
                return data["results"][0]["id"]

            # Третья попытка: поиск без указания языка (оригинальное название)
            params.pop("language", None)
            data = await self.fetch_json(session, url, params)
            if data and "results" in data and data["results"]:
                self.stdout.write(self.style.SUCCESS(f"Найден TMDB ID для фильма '{title}' (оригинальное): {data['results'][0]['id']}"))
                return data["results"][0]["id"]

            self.stdout.write(self.style.WARNING(f"Не удалось найти TMDB ID для фильма: {title} (попытки на ru-RU, en-US и оригинальном языке)"))
            return None

    async def fetch_movie_details(self, session, tmdb_id, semaphore):
        """Получает детальную информацию о фильме, включая актеров и съемочную группу."""
        url = f"{BASE_URL}/movie/{tmdb_id}"
        params = {"api_key": API_KEY, "language": "ru-RU", "append_to_response": "credits"}
        async with semaphore:
            return await self.fetch_json(session, url, params)

    async def search_person(self, session, name, semaphore):
        """Ищет человека (актера) в TMDB по имени."""
        url = f"{BASE_URL}/search/person"
        params = {
            "api_key": API_KEY,
            "language": "ru-RU",
            "query": urllib.parse.quote(name),
            "page": 1
        }
        async with semaphore:
            data = await self.fetch_json(session, url, params)
            if data and "results" in data and data["results"]:
                return data["results"][0]["id"]
            return None

    async def rewrite_movie_actors_and_credits(self, session, movie, semaphore):
        """Переписывает связи актеров и добавляет режиссеров/сценаристов для фильма."""
        try:
            # Ищем tmdb_id для фильма по названию и году выпуска
            tmdb_id = await self.search_movie(session, movie.title, movie.release_date, semaphore)
            if not tmdb_id:
                return

            # Получаем данные о фильме из TMDB
            data = await self.fetch_movie_details(session, tmdb_id, semaphore)
            if not data or "status_code" in data:
                self.stdout.write(self.style.WARNING(f"Не удалось получить данные для фильма: {movie.title} (TMDB ID: {tmdb_id})"))
                return

            cast = data.get("credits", {}).get("cast", [])
            crew = data.get("credits", {}).get("crew", [])

            # Обрабатываем актеров
            actors = []
            for actor_data in cast:  # Ограничиваем до 10 актеров
                photo_path = actor_data.get("profile_path")
                if not photo_path:  # Пропускаем актеров без фото
                    continue

                # Ищем актера в базе по имени
                actor_name = actor_data["name"]
                actor = await sync_to_async(Actor.objects.filter(name=actor_name).first)()
                if not actor:
                    # Если актера нет, создаем его
                    actor = await sync_to_async(Actor.objects.create)(
                        name=actor_name,
                        photo_url=f"https://image.tmdb.org/t/p/w500{photo_path}"
                    )
                actors.append(actor)

            # Переписываем связи актеров с фильмом
            await sync_to_async(movie.actors.set)(actors)
            self.stdout.write(self.style.SUCCESS(f"Обновлены актеры ({len(actors)}) для фильма: {movie.title}"))

            # Обрабатываем режиссеров и сценаристов
            directors_count = 0
            writers_count = 0
            for crew_member in crew:
                role = crew_member.get("job")
                if role not in ["Director", "Writer"]:  # Обрабатываем только режиссеров и сценаристов
                    continue

                person_name = crew_member["name"]
                person_tmdb_id = crew_member["id"]
                photo_path = crew_member.get("profile_path", "")

                # Создаем или получаем Person
                person, _ = await sync_to_async(Person.objects.get_or_create)(
                    tmdb_id=person_tmdb_id,
                    defaults={
                        "name": person_name,
                        "photo_url": f"https://image.tmdb.org/t/p/w500{photo_path}" if photo_path else ""
                    }
                )

                # Создаем запись в MovieCredit
                await sync_to_async(MovieCredit.objects.get_or_create)(
                    movie=movie,
                    person=person,
                    role=role,
                    department=crew_member.get("department", ""),
                )

                if role == "Director":
                    directors_count += 1
                elif role == "Writer":
                    writers_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Добавлены режиссеры ({directors_count}) и сценаристы ({writers_count}) для фильма: {movie.title}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка обработки фильма {movie.title}: {str(e)}"))

    async def rewrite_all_movies(self):
        """Основной метод для переписывания связей."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession() as session:
            # Получаем все фильмы
            movies = await sync_to_async(list)(Movie.objects.all())
            self.stdout.write(f"Всего фильмов для обработки: {len(movies)}")

            # Обрабатываем фильмы параллельно
            tasks = [self.rewrite_movie_actors_and_credits(session, movie, semaphore) for movie in movies]
            await asyncio.gather(*tasks)

    def handle(self, *args, **options):
        """Запускает процесс переписывания связей."""
        self.stdout.write("Очищаем существующие связи фильмов и актеров...")
        movies = Movie.objects.all()
        for movie in movies:
            movie.actors.clear()
        self.stdout.write("Очищаем существующие записи в MovieCredit...")
        MovieCredit.objects.all().delete()
        self.stdout.write("Начинаем переписывание связей фильмов, актеров и добавление режиссеров/сценаристов...")
        asyncio.run(self.rewrite_all_movies())
        self.stdout.write(self.style.SUCCESS("Переписывание связей завершено!"))