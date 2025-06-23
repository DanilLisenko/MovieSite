# users/management/commands/populate_fake_data.py
import random
import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from movies.models import Movie, Review, Genre
from django.utils import timezone

CustomUser = get_user_model()
fake = Faker('ru_RU')

class Command(BaseCommand):
    help = 'Создаёт 1000 фейковых пользователей и по 5 ботоподобных отзывов для каждого фильма'

    def handle(self, *args, **kwargs):
        if not Genre.objects.exists():
            self.stdout.write(self.style.WARNING("Нет жанров в базе данных. Создайте жанры перед выполнением команды."))
            return

        # Создание пользователей
        self.stdout.write("Создание 1000 фейковых пользователей...")
        start_time = time.time()
        existing_usernames = set(CustomUser.objects.values_list('username', flat=True))
        existing_emails = set(CustomUser.objects.values_list('email', flat=True))
        users = []
        for i in range(1000):
            username = fake.user_name()
            while username in existing_usernames:
                username = fake.user_name() + str(random.randint(1, 1000))
            email = fake.email()
            while email in existing_emails:
                email = fake.email()
            existing_usernames.add(username)
            existing_emails.add(email)
            user = CustomUser(
                username=username,
                email=email,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                favorite_genre=random.choice(Genre.objects.all()),
                bio=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                is_admin=False,
                is_blocked=False,
                is_active=False,
                password='fake'
            )
            users.append(user)
            if (i + 1) % 100 == 0:
                self.stdout.write(f"Создано {i + 1} пользователей... ({time.time() - start_time:.2f} сек)")

        try:
            self.stdout.write("Выполняется массовая вставка пользователей...")
            batch_size = 100
            for i in range(0, len(users), batch_size):
                CustomUser.objects.bulk_create(users[i:i + batch_size])
                self.stdout.write(f"Вставлено {i + batch_size} пользователей...")
            self.stdout.write(self.style.SUCCESS(f"Создано {len(users)} пользователей за {time.time() - start_time:.2f} сек"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при создании пользователей: {e}"))
            return

        # Создание отзывов
        self.stdout.write("Создание отзывов...")
        review_start_time = time.time()
        bot_reviews = [
            "Классный фильм, всем советую!",
            "Захватывающий сюжет, смотрел не отрываясь!",
            "Актёры молодцы, но немного затянуто.",
            "Хороший фильм, но концовка предсказуемая.",
            "Нормально, но ждал большего.",
            "Просто супер, эмоции на высоте!",
            "Интересный фильм, стоит посмотреть.",
            "Обычный фильм, ничего особенного.",
            "Вау, это было круто!",
            "Разок посмотреть можно, но не шедевр."
        ]

        reviews = []
        existing_reviews = set(Review.objects.values_list('user_id', 'movie_id'))
        all_users = list(CustomUser.objects.all())  # Загружаем пользователей один раз
        movies = Movie.objects.all()
        if not movies:
            self.stdout.write(self.style.WARNING("Нет фильмов в базе данных. Создайте фильмы перед добавлением отзывов."))
            return

        for i, movie in enumerate(movies, 1):
            selected_users = random.sample(all_users, min(5, len(all_users)))
            for user in selected_users:
                if (user.id, movie.id) not in existing_reviews:
                    review = Review(
                        user=user,
                        movie=movie,
                        review_text=random.choice(bot_reviews),
                        rating=random.randint(3, 10),
                        created_at=timezone.now()
                    )
                    reviews.append(review)
                    existing_reviews.add((user.id, movie.id))
            if i % 1000 == 0:  # Логируем каждые 1000 фильмов
                self.stdout.write(f"Обработано {i} фильмов... ({time.time() - review_start_time:.2f} сек)")

        try:
            self.stdout.write("Выполняется массовая вставка отзывов...")
            batch_size = 1000
            for i in range(0, len(reviews), batch_size):
                Review.objects.bulk_create(reviews[i:i + batch_size])
                self.stdout.write(f"Вставлено {i + batch_size} отзывов...")
            self.stdout.write(self.style.SUCCESS(f"Создано {len(reviews)} отзывов за {time.time() - review_start_time:.2f} сек"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при создании отзывов: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("Генерация фейковых данных завершена!"))