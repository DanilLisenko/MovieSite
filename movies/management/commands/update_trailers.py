import asyncio
import aiohttp
from aiohttp import ClientTimeout
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from movies.models import Movie
import time
import logging

API_KEY = "8bf31002475b2fd4bc514cd9d272c4e5"
BASE_URL = "https://api.themoviedb.org/3"
MAX_CONCURRENT_REQUESTS = 30

logging.basicConfig(
    filename='trailer_urls_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Command(BaseCommand):
    help = "Update trailer_urls for movies that already have a trailer_url"

    async def fetch_json(self, session, url, params=None, retries=3):
        timeout = ClientTimeout(total=30)
        for attempt in range(retries):
            try:
                async with session.get(url, params=params, timeout=timeout) as response:
                    response.raise_for_status()
                    return await response.json()
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
                logging.error(f"Ошибка после {retries} попыток для {url}: {str(e)}")
                return None
        return None

    async def fetch_movie_videos(self, session, tmdb_id, semaphore, language=None):
        url = f"{BASE_URL}/movie/{tmdb_id}/videos"
        params = {"api_key": API_KEY}
        if language:
            params["language"] = language
        async with semaphore:
            return await self.fetch_json(session, url, params)

    async def update_movie_trailers(self, session, movie, semaphore):
        try:
            # Пропускаем фильмы без trailer_url
            if not movie.trailer_url or not movie.trailer_url.strip():
                return

            tmdb_id = movie.tmdb_id
            if not tmdb_id:
                logging.warning(f"TMDB ID отсутствует для '{movie.title}' (ID: {movie.id})")
                return

            trailer_urls = []
            # Шаг 1: Пробуем русский язык
            ru_data = await self.fetch_movie_videos(session, tmdb_id, semaphore, language="ru-RU")
            if ru_data and "results" in ru_data:
                for video in ru_data["results"]:
                    if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                        trailer_urls.append(f"https://www.youtube.com/watch?v={video['key']}")

            # Шаг 2: Пробуем английский язык
            en_data = await self.fetch_movie_videos(session, tmdb_id, semaphore, language="en-US")
            if en_data and "results" in en_data:
                for video in en_data["results"]:
                    if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                        trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                        if trailer_url not in trailer_urls:
                            trailer_urls.append(trailer_url)

            # Шаг 3: Пробуем все языки
            all_data = await self.fetch_movie_videos(session, tmdb_id, semaphore)
            if all_data and "results" in all_data:
                for video in all_data["results"]:
                    if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                        trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                        if trailer_url not in trailer_urls:
                            trailer_urls.append(trailer_url)

            # Обновляем trailer_urls, если найдены трейлеры
            if trailer_urls:
                movie.trailer_urls = trailer_urls
                await sync_to_async(movie.save)()
                logging.info(f"Обновлены трейлеры для '{movie.title}' (TMDB ID: {tmdb_id}): {trailer_urls}")
            else:
                logging.warning(f"Трейлеры не найдены для TMDB ID {tmdb_id} (ID: {movie.id})")

        except Exception as e:
            logging.error(f"Ошибка обработки фильма ID {movie.id}: {str(e)}")

    async def update_trailers(self):
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        movies = await sync_to_async(list)(
            Movie.objects.filter(trailer_url__isnull=False).exclude(trailer_url="")
        )
        logging.info(f"Найдено {len(movies)} фильмов с трейлерами для обновления")

        async with aiohttp.ClientSession() as session:
            tasks = [self.update_movie_trailers(session, movie, semaphore) for movie in movies]
            await asyncio.gather(*tasks)

    def handle(self, *args, **options):
        start_time = time.time()
        logging.info("Начинаем обновление списка трейлеров")
        asyncio.run(self.update_trailers())
        elapsed_time = time.time() - start_time
        logging.info(f"Обновление завершено за {elapsed_time:.2f} секунд")