import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from movies.models import Movie, Review
from users.models import CustomUser  # Импорт модели пользователей

class Command(BaseCommand):
    help = 'Генерирует случайные отзывы для фильмов, вышедших за последние 2 месяца'

    def handle(self, *args, **options):
        # Определяем дату два месяца назад (примерно 60 дней)
        two_months_ago = date.today() - timedelta(days=60)
        movies = Movie.objects.filter(release_date__gte=two_months_ago)

        # Получаем всех пользователей (предполагается, что их достаточно)
        users = list(CustomUser.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("В базе нет пользователей. Создайте хотя бы одного."))
            return

        for movie in movies:
            # Генерируем случайное число отзывов от 15 до 100
            review_count = random.randint(15, 100)
            self.stdout.write(f"Генерирую {review_count} отзывов для фильма: {movie.title}")

            # Чтобы не допустить повторных отзывов одного и того же пользователя,
            # будем отслеживать id пользователей, оставивших отзыв для данного фильма.
            used_user_ids = set()

            for i in range(review_count):
                # Выбираем случайного пользователя, который ещё не оставил отзыв для этого фильма
                available_users = [u for u in users if u.id not in used_user_ids]
                if not available_users:
                    self.stdout.write("Недостаточно уникальных пользователей для отзыва.")
                    break

                user = random.choice(available_users)
                used_user_ids.add(user.id)

                # Генерируем рейтинг отзыва, близкий к рейтингу фильма
                # Например, смещение в диапазоне от -1 до +1
                offset = random.uniform(-1, 1)
                review_rating = movie.rating + offset
                # Ограничиваем значение от 1 до 10
                review_rating = max(1, min(10, review_rating))
                review_rating = round(review_rating)

                # Выбираем текст отзыва в зависимости от полученной оценки
                if review_rating >= 8:
                    review_text = random.choice([
                        "Отлично!", "Превосходно!", "Великолепно!", "Замечательно!"
                    ])
                elif review_rating >= 5:
                    review_text = random.choice([
                        "Неплохо", "Хорошо", "Средне", "Можно лучше"
                    ])
                else:
                    review_text = random.choice([
                        "Ужасно", "Очень плохо", "Отвратительно", "Плохо"
                    ])

                # Создаём отзыв (согласно ограничению unique_together для (user, movie))
                review, created = Review.objects.get_or_create(
                    user=user,
                    movie=movie,
                    defaults={
                        'rating': review_rating,
                        'review_text': review_text
                    }
                )
                if created:
                    self.stdout.write(f"Создан отзыв для пользователя {user.username}")
                else:
                    self.stdout.write(f"Отзыв уже существует для пользователя {user.username} на фильм {movie.title}")

            self.stdout.write(self.style.SUCCESS(f"Завершено для фильма: {movie.title}"))
