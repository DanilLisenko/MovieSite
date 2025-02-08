import string
import random
from django.core.management.base import BaseCommand
from users.models import CustomUser  # Убедитесь, что импортируете вашу модель пользователя
from django.utils.crypto import get_random_string

class Command(BaseCommand):
    help = 'Создает 100 фиктивных пользователей'

    def handle(self, *args, **options):
        count = 100  # Количество пользователей для создания
        created_users = 0

        for i in range(count):
            # Генерируем случайное имя пользователя: например, "user" + случайная строка из 6 символов
            random_str = get_random_string(length=6, allowed_chars=string.ascii_lowercase + string.digits)
            username = f"user_{random_str}"
            email = f"{username}@example.com"
            password = "password"  # Для всех пользователей одинаковый пароль для тестирования

            # Проверяем, существует ли уже пользователь с таким именем, чтобы избежать дублирования
            if not CustomUser.objects.filter(username=username).exists():
                CustomUser.objects.create_user(username=username, email=email, password=password)
                created_users += 1
                self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Пользователь {username} уже существует. Пропускаем."))

        self.stdout.write(self.style.SUCCESS(f"Генерация пользователей завершена. Создано {created_users} новых пользователей."))
