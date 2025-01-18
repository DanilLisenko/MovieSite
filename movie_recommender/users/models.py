from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    favorite_genre = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)  # Новое поле

User = get_user_model()

class WatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched_movies')
    title = models.CharField(max_length=255)
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SavedMovie(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_movies')
    title = models.CharField(max_length=255)  # Название фильма
    added_at = models.DateTimeField(auto_now_add=True)  # Дата добавления

    def __str__(self):
        return self.title
