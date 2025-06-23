from django.core.management.base import BaseCommand
from movies.models import Movie, Actor
import re

class Command(BaseCommand):
    help = 'Удаляет фильмы и актеров с названиями/именами не на русском или английском языке'

    def is_valid_name(self, name):
        # Проверяем, содержит ли строка хотя бы одну русскую или английскую букву
        return bool(re.search(r'[a-zA-Zа-яА-Я]', name))

    def handle(self, *args, **kwargs):
        # Очистка фильмов
        movies = Movie.objects.all()
        deleted_movies = 0
        for movie in movies:
            if not self.is_valid_name(movie.title):
                self.stdout.write(f"Удаляем фильм: {movie.title}")
                movie.delete()
                deleted_movies += 1
            else:
                self.stdout.write(f"Сохраняем фильм: {movie.title}")

        # Очистка актеров
        actors = Actor.objects.all()
        deleted_actors = 0
        for actor in actors:
            if not self.is_valid_name(actor.name):
                self.stdout.write(f"Удаляем актера: {actor.name}")
                actor.delete()
                deleted_actors += 1
            else:
                self.stdout.write(f"Сохраняем актера: {actor.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Очистка завершена. Удалено {deleted_movies} фильмов и {deleted_actors} актеров."
            )
        )