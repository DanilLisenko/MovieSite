from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):

    bio = models.TextField(blank=True, null=True, help_text="Биография пользователя")
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, help_text="Фото профиля")
    is_admin = models.BooleanField(default=False, help_text="Отмечает пользователя как администратора")
    is_blocked = models.BooleanField(default=False, help_text="Блокирует доступ пользователя к сайту")

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Синхронизируем is_active с is_blocked
        if self.is_blocked:
            self.is_active = False
        super().save(*args, **kwargs)

    class Meta:
        permissions = [
            ("can_block_user", "Может блокировать пользователей"),
            ("can_delete_review", "Может удалять отзывы"),
        ]

