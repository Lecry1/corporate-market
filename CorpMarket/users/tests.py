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


# Тесты успешной регистрации
class RegistrationSuccessTest(BaseUserTest):

    # Проверка создания нового пользователя
    def test_register_new_user(self):
        response = self.client.post(
            self.register_url, {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertRedirects(response, self.adverts_list_url)

    # После регистрации пользователь автоматически входит
    def test_user_is_authenticated_after_register(self):
        response = self.client.post(
            self.register_url, {
                'username': 'fulluser',
                'email': 'full@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            }
        )
        user = User.objects.first()
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, user)


# Тесты входа в аккаунт
class LoginTest(BaseUserTest):

    def setUp(self):
        super().setUp()
        self.test_user = self.create_test_user(username='logintest', password='LoginPass123!')

    # Проверка успешного входа
    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'username': 'logintest',
            'password': 'LoginPass123!',
        })
        self.assertRedirects(response, self.adverts_list_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'logintest')

    # Нельзя войти с неверным паролем
    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            'username': 'logintest',
            'password': 'WrongPassword!',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'Please enter a correct username and password.')
