from django.db import models
from django.contrib.auth import get_user_model
from googletrans import Translator

User = get_user_model()  # Вместо прямого импорта CustomUser

class Person(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)

class MovieCredit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    character = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(default=0)
    poster_url = models.URLField(blank=True)

    def __str__(self):
        return self.title


class UserMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Используем get_user_model()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)
    watchlist = models.BooleanField(default=False)


class Review(models.Model):
    """
    Модель для отзывов пользователей на фильмы.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')  # Используем get_user_model()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    review_text = models.TextField(blank=True)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'movie'),)

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.movie.title}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Используем get_user_model()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

class Actor(models.Model):
    name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='actors/', blank=True, null=True)
    movies = models.ManyToManyField(Movie, related_name="actors")

    def __str__(self):
        return self.name
