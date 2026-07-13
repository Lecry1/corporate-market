from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from users.models import Admin, CustomUser

User = get_user_model()

# ==========================================
# ТЕСТЫ МОДЕЛЕЙ (из ветки dev)
# ==========================================


class CustomUserModelTest(TestCase):

    def test_user_creation_and_string_representation(self):
        password = 'safe-password-2026'
        user = CustomUser.objects.create_user(
            username='alex',
            password=password,
            first_name='Александр',
            last_name='Гущин',
        )

        self.assertEqual(str(user), 'alex')
        self.assertEqual(user.display_name, 'Александр Гущин')
        self.assertEqual(user.buyer_rating, 0.0)
        self.assertEqual(user.seller_rating, 0.0)
        self.assertTrue(user.check_password(password))


class AdminModelTest(TestCase):

    def test_admin_creation_and_string_representation(self):
        user = CustomUser.objects.create_user(username='administrator')
        administrator = Admin.objects.create(user=user)

        self.assertEqual(administrator.pk, user.pk)
        self.assertEqual(administrator.user, user)
        self.assertEqual(user.admin_profile, administrator)
        self.assertTrue(user.is_market_admin)
        self.assertEqual(str(administrator), 'Администратор administrator')


# ==========================================
# ТЕСТЫ ВЬЮХ И АУТЕНТИФИКАЦИИ (из ветки tests)
# ==========================================


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

    def test_register_page_accessible(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_login_page_accessible(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_logout_requires_post(self):
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)


# Тесты успешной регистрации
class RegistrationSuccessTest(BaseUserTest):

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

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'username': 'logintest',
            'password': 'LoginPass123!',
        })
        self.assertRedirects(response, self.adverts_list_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'logintest')

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            'username': 'logintest',
            'password': 'WrongPassword!',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'Пожалуйста, введите правильные имя пользователя и пароль')


# Тесты выхода из аккаунта
class LogoutTest(BaseUserTest):

    def setUp(self):
        super().setUp()
        self.test_user = self.create_test_user(username='logouttest', password='LogoutPass123!')
        self.client.login(username='logouttest', password='LogoutPass123!')

    def test_logout_redirect_with_post(self):
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.adverts_list_url)

    def test_user_logged_out_after_logout(self):
        self.client.post(self.logout_url)
        response = self.client.get(self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_get_returns_405(self):
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 405)


# Тест автоматического входа после регистрации
class RegistrationAutoLoginTest(BaseUserTest):

    def test_user_auto_login_after_registration(self):
        response = self.client.post(
            self.register_url, {
                'username': 'autologin',
                'email': 'auto@example.com',
                'password1': 'AutoPass123!',
                'password2': 'AutoPass123!',
            }
        )
        user = User.objects.first()
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, user)
