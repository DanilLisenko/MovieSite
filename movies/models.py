from django.db import models
from django.contrib.auth import get_user_model
from googletrans import Translator
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser

User = get_user_model()

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
    search_vector = SearchVectorField(null=True, blank=True)
    trailer_url = models.URLField(blank=True, null=True)
    trailer_urls = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['rating']),
            models.Index(fields=['release_date']),
            GinIndex(fields=['search_vector'], name='movie_search_idx'),
            GinIndex(fields=['title'], name='movie_title_trgm_idx', opclasses=['gin_trgm_ops']),  # Для опечаток
        ]


class UserMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Используем get_user_model()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)
    watchlist = models.BooleanField(default=False)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    review_text = models.TextField(blank=True)
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён")

    class Meta:
        unique_together = (('user', 'movie'),)
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

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
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)  # Уникальный ID из TMDB
    name = models.CharField(max_length=255)  # Имя актера
    birth_date = models.DateField(null=True, blank=True)  # Дата рождения
    bio = models.TextField(blank=True)  # Биография
    photo_url = models.URLField(blank=True)  # Ссылка на фото (заменили ImageField на URLField)
    movies = models.ManyToManyField(Movie, related_name="actors")  # Связь с фильмами
    search_vector = SearchVectorField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            GinIndex(fields=['search_vector'], name='actor_search_idx'),
            GinIndex(fields=['name'], name='actor_name_trgm_idx', opclasses=['gin_trgm_ops']),  # Для опечаток
        ]

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.query}"

@receiver(post_save, sender=Movie)
def update_movie_search_vector(sender, instance, **kwargs):
    Movie.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('title', weight='A', config='russian') +
                     SearchVector('description', weight='B', config='russian')
    )

@receiver(post_save, sender=Actor)
def update_actor_search_vector(sender, instance, **kwargs):
    Actor.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('name', weight='A', config='russian') +
                     SearchVector('bio', weight='B', config='russian')
    )

# movies/models.py
class FavoriteActor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_actors')
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'actor')  # Пользователь не может добавить одного актера дважды

    def __str__(self):
        return f"{self.user.username} - {self.actor.name}"