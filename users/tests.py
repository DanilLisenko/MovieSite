from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterViewTest(TestCase):
    def test_register_user(self):
        url = reverse('users:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:genre_preferences'))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_authenticated)

    def test_register_page_loads(self):
        url = reverse('users:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_blocked_user(self):
        user = User.objects.create_user(username='blockeduser', password='password123')
        user.is_blocked = True
        user.save()
        self.assertFalse(user.is_active)

    def test_register_invalid_passwords(self):
        url = reverse('users:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'differentpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Остаемся на странице
        self.assertEqual(User.objects.count(), 0)  # Пользователь не создан