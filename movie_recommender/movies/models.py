from django.db import models
from users.models import CustomUser
from googletrans import Translator


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(default=0)
    poster_url = models.URLField(blank=True)

    def __str__(self):
        return self.title

    def translate_fields(self):
        translator = Translator()
        try:
            self.title = translator.translate(self.title, src='en', dest='ru').text
            self.description = translator.translate(self.description, src='en', dest='ru').text
            self.save()
        except Exception as e:
            print(f"Ошибка перевода: {e}")

class UserMovie(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)
    watchlist = models.BooleanField(default=False)




class Review(models.Model):
    """
    Модель для отзывов пользователей на фильмы.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    review_text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.movie.title}"


class Watchlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched = models.BooleanField(default=False)  # Флаг, просмотрен ли фильм
    added_at = models.DateTimeField(auto_now_add=True)  # Время добавления

    class Meta:
        unique_together = ('user', 'movie')