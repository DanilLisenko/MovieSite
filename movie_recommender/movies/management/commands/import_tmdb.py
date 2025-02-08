import requests
from django.core.management.base import BaseCommand
from movies.models import Movie, Person, MovieCredit


class Command(BaseCommand):
    help = 'Import movie credits from TMDB'

    def handle(self, *args, **options):
        for movie in Movie.objects.filter(tmdb_id__isnull=False):
            self.import_credits(movie)

    def import_credits(self, movie):
        url = f"https://api.themoviedb.org/3/movie/{movie.tmdb_id}/credits"
        params = {'api_key': '8bf31002475b2fd4bc514cd9d272c4e5'}
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            self.process_cast(movie, data.get('cast', []))
            self.process_crew(movie, data.get('crew', []))

    def process_cast(self, movie, cast):
        for member in cast[:5]:  # Берем первых 5 актеров
            person, _ = Person.objects.get_or_create(
                tmdb_id=member['id'],
                defaults={
                    'name': member['name'],
                    'photo_url': f"https://image.tmdb.org/t/p/w200{member['profile_path']}" if member[
                        'profile_path'] else ''
                }
            )
            MovieCredit.objects.get_or_create(
                movie=movie,
                person=person,
                role='Actor',
                character=member['character']
            )

    def process_crew(self, movie, crew):
        for member in crew:
            if member['job'] == 'Director':
                person, _ = Person.objects.get_or_create(
                    tmdb_id=member['id'],
                    defaults={
                        'name': member['name'],
                        'photo_url': f"https://image.tmdb.org/t/p/w200{member['profile_path']}" if member[
                            'profile_path'] else ''
                    }
                )
                MovieCredit.objects.get_or_create(
                    movie=movie,
                    person=person,
                    role='Director',
                    department=member['department']
                )