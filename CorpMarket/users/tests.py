from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


# Базовый класс с общими методами для тестов
class BaseUserTest(TestCase):

    def setUp(self):
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        self.adverts_list_url = reverse('adverts:list')

    def create_test_user(self, username='testuser', password='StrongPass123!'):
        return User.objects.create_user(username=username, email='test@example.com', password=password)


# Тесты доступности страниц аутентификации
class AuthPageTest(BaseUserTest):

    # Страница регистрации должна быть доступна
    def test_register_page_accessible(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    # Страница входа должна быть доступна
    def test_login_page_accessible(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    # Выход должен требовать POST запрос
    def test_logout_requires_post(self):
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)
