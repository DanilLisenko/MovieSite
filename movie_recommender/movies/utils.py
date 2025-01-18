import requests
from .models import Movie
from googletrans import Translator

def fetch_and_save_movies():
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
                movie, created = Movie.objects.get_or_create(
                    title=item['title'],
                    defaults={
                        'description': item.get('overview', ''),
                        'genre': 'Unknown',  # Вы можете настроить сопоставление жанров
                        'release_date': item.get('release_date', None),
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



def translate_to_russian(text):
    if not isinstance(text, str):  # Проверка типа
        return str(text)
    translator = Translator()
    try:
        translated = translator.translate(text, src='en', dest='ru')
        return translated.text
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text


def translate_movie_fields(movie):
    movie.title = translate_to_russian(movie.title)
    movie.description = translate_to_russian(movie.description)
    movie.save()
