from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from users.forms import CustomUserCreationForm, UserProfileUpdateForm
from users.models import Admin, CustomUser

User = get_user_model()

# ==========================================
# ТЕСТЫ МОДЕЛЕЙ
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

    def test_database_rejects_duplicate_email_case_insensitively(self):
        CustomUser.objects.create_user(username="first", email="duplicate@example.com")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CustomUser.objects.create_user(username="second", email="DUPLICATE@EXAMPLE.COM")

    def test_database_allows_multiple_users_without_email(self):
        first_user = CustomUser.objects.create_user(username="first_without_email")
        second_user = CustomUser.objects.create_user(username="second_without_email")

        self.assertEqual(first_user.email, "")
        self.assertEqual(second_user.email, "")
        self.assertEqual(CustomUser.objects.filter(email="").count(), 2)


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
# ТЕСТЫ ФОРМ
# ==========================================


class CustomUserCreationFormTest(TestCase):

    def setUp(self):
        self.valid_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }

    def test_valid_form(self):
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_email_required(self):
        data = self.valid_data.copy()
        data['email'] = ''
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_uniqueness(self):
        CustomUser.objects.create_user(username='existing', email='existing@example.com', password='Pass123!')
        data = self.valid_data.copy()
        data['email'] = 'existing@example.com'
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'Пользователь с таким email уже существует')

    def test_email_uniqueness_case_insensitive(self):
        CustomUser.objects.create_user(username='existing', email='existing@example.com', password='Pass123!')
        data = self.valid_data.copy()
        data['email'] = 'EXISTING@EXAMPLE.COM'
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123!'
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_password_too_short(self):
        data = self.valid_data.copy()
        data['password1'] = 'short'
        data['password2'] = 'short'
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_email_normalization(self):
        data = self.valid_data.copy()
        data['email'] = 'New.User@Example.COM'
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'new.user@example.com')


class UserProfileUpdateFormTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', email='test@example.com', password='Pass123!')
        self.valid_data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'new@example.com',
            'phone_number': '+79001234567',
            'address': 'Москва, ул. Тестовая, д. 1',
        }

    def test_valid_form(self):
        form = UserProfileUpdateForm(data=self.valid_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_email_uniqueness(self):
        CustomUser.objects.create_user(username='other', email='other@example.com', password='Pass123!')
        data = self.valid_data.copy()
        data['email'] = 'other@example.com'
        form = UserProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'Пользователь с таким email уже существует.')

    def test_clean_email_case_insensitive(self):
        CustomUser.objects.create_user(username='other', email='other@example.com', password='Pass123!')
        data = self.valid_data.copy()
        data['email'] = 'OTHER@EXAMPLE.COM'
        form = UserProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_clean_email_allows_own_email(self):
        data = self.valid_data.copy()
        data['email'] = 'test@example.com'
        form = UserProfileUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_clean_email_required(self):
        data = self.valid_data.copy()
        data['email'] = ''
        form = UserProfileUpdateForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_clean_email_normalization(self):
        data = self.valid_data.copy()
        data['email'] = 'New.User@Example.COM'
        form = UserProfileUpdateForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'new.user@example.com')


class MessageFormTest(TestCase):

    def setUp(self):
        from adverts.models import Advert
        from chats.forms import MessageForm
        from chats.models import Chat

        self.MessageForm = MessageForm
        self.seller = CustomUser.objects.create_user(username='seller')
        self.buyer = CustomUser.objects.create_user(username='buyer')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Тест',
            description='Описание',
            category=Advert.Category.PRODUCT,
        )
        self.chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)

    def test_valid_message_form(self):
        data = {'text': 'Привет! Как дела?'}
        form = self.MessageForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_message_invalid(self):
        data = {'text': ''}
        form = self.MessageForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_whitespace_message_invalid(self):
        data = {'text': '   '}
        form = self.MessageForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_message_too_long_invalid(self):
        data = {'text': 'A' * 10001}
        form = self.MessageForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)


# ==========================================
# ТЕСТЫ ВЬЮХ И АУТЕНТИФИКАЦИИ
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


class RegistrationEmailUniquenessTest(BaseUserTest):

    def setUp(self):
        super().setUp()
        User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="StrongPass123!",
        )

    def test_registration_rejects_duplicate_email(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "another_user",
                "email": "existing@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, "Пользователь с таким email уже существует.")

    def test_registration_rejects_duplicate_email_with_other_case(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "another_user",
                "email": "EXISTING@EXAMPLE.COM",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, "Пользователь с таким email уже существует.")

    def test_registration_normalizes_email_to_lowercase(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "new_user",
                "email": "New.User@Example.COM",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, self.adverts_list_url)
        user = User.objects.get(username="new_user")
        self.assertEqual(user.email, "new.user@example.com")


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
        self.assertContains(response, 'Неверное имя пользователя или пароль')


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
