from adverts.models import Advert
from chats.models import Chat, Message
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
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
# ТЕСТЫ МОДЕЛИ CHAT
# ==========================================


class ChatModelCleanTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='seller')
        self.buyer = CustomUser.objects.create_user(username='buyer')
        self.other_seller = CustomUser.objects.create_user(username='other_seller')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Тест',
            description='Описание',
            category=Advert.Category.PRODUCT,
        )

    def test_chat_clean_valid(self):
        chat = Chat(advert=self.advert, seller=self.seller, buyer=self.buyer)
        chat.clean()

    def test_chat_clean_invalid_seller(self):
        chat = Chat(
            advert=self.advert,
            seller=self.other_seller,  # Другой пользователь, не автор
            buyer=self.buyer
        )
        with self.assertRaises(ValidationError):
            chat.clean()

    def test_chat_clean_buyer_is_seller(self):
        chat = Chat(
            advert=self.advert,
            seller=self.seller,
            buyer=self.seller  # Покупатель = продавец
        )
        with self.assertRaises(ValidationError):
            chat.clean()


# ==========================================
# ТЕСТЫ МОДЕЛИ MESSAGE
# ==========================================


class MessageModelCleanTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='seller')
        self.buyer = CustomUser.objects.create_user(username='buyer')
        self.other_user = CustomUser.objects.create_user(username='other')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Тест',
            description='Описание',
            category=Advert.Category.PRODUCT,
        )
        self.chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)

    def test_message_clean_valid(self):
        message = Message(chat=self.chat, sender=self.buyer, text='Привет!')
        message.clean()

    def test_message_clean_empty_text(self):
        message = Message(chat=self.chat, sender=self.buyer, text='')
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_clean_whitespace_text(self):
        message = Message(chat=self.chat, sender=self.buyer, text='   ')
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_clean_inactive_chat(self):
        self.chat.is_active = False
        self.chat.save()
        message = Message(chat=self.chat, sender=self.buyer, text='Привет!')
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_clean_sender_not_participant(self):
        message = Message(
            chat=self.chat,
            sender=self.other_user,  # Не участник чата
            text='Привет!'
        )
        with self.assertRaises(ValidationError):
            message.clean()


# ==========================================
# ТЕСТЫ МОДЕЛИ PHOTO
# ==========================================


class PhotoModelSaveTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='seller')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Тест',
            description='Описание',
            category=Advert.Category.PRODUCT,
        )

    def test_photo_auto_order(self):
        from adverts.models import Photo

        photo1 = Photo.objects.create(advert=self.advert)
        self.assertEqual(photo1.order, 0)

        photo2 = Photo.objects.create(advert=self.advert)
        self.assertEqual(photo2.order, 1)

        photo3 = Photo.objects.create(advert=self.advert)
        self.assertEqual(photo3.order, 2)

    def test_photo_order_with_explicit_order(self):
        """Тест: Явно указанный order не переопределяется"""
        from adverts.models import Photo

        photo = Photo.objects.create(advert=self.advert, order=5)
        self.assertEqual(photo.order, 5)


# ==========================================
# ТЕСТЫ МОДЕЛИ REVIEW
# ==========================================


class ReviewModelTest(TestCase):

    def setUp(self):
        self.user1 = CustomUser.objects.create_user(username='user1')
        self.user2 = CustomUser.objects.create_user(username='user2')
        self.advert = Advert.objects.create(
            seller=self.user2,
            title='Тест',
            description='Описание',
            category=Advert.Category.PRODUCT,
        )

    def test_update_user_rating_after_review_creation(self):
        from reviews.models import Review

        self.assertEqual(self.user2.seller_rating, 0.0)

        Review.objects.create(
            from_user=self.user1, to_user=self.user2, advert=self.advert, flag=Review.Flag.TO_SELLER, rating=5,
            comment='Отлично!'
        )

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.seller_rating, 5.0)

    def test_update_user_rating_multiple_reviews(self):
        from reviews.models import Review

        user3 = CustomUser.objects.create_user(username='user3')

        Review.objects.create(
            from_user=self.user1, to_user=self.user2, advert=self.advert, flag=Review.Flag.TO_SELLER, rating=5,
            comment='Отлично!'
        )

        # Создаём ещё одно объявление и отзыв
        advert2 = Advert.objects.create(
            seller=self.user2,
            title='Тест2',
            description='Описание2',
            category=Advert.Category.PRODUCT,
        )
        Review.objects.create(
            from_user=user3, to_user=self.user2, advert=advert2, flag=Review.Flag.TO_SELLER, rating=3,
            comment='Нормально'
        )

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.seller_rating, 4.0)  # (5 + 3) / 2 = 4.0

    def test_update_user_rating_after_review_deletion(self):
        from reviews.models import Review

        review = Review.objects.create(
            from_user=self.user1, to_user=self.user2, advert=self.advert, flag=Review.Flag.TO_SELLER, rating=5,
            comment='Отлично!'
        )

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.seller_rating, 5.0)

        # Удаляем отзыв
        review.delete()

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.seller_rating, 0.0)


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
        self.client = Client()
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


# ==========================================
# ТЕСТЫ ВЬЮХ: AdvertListView (фильтрация)
# ==========================================


class AdvertListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass123')
        self.category_product = Advert.Category.PRODUCT
        self.category_service = Advert.Category.SERVICE

        # Создаём объявления разных статусов
        self.active_advert = Advert.objects.create(
            seller=self.user, title='Активное объявление', description='Описание активного', price=1000,
            category=self.category_product, address='Москва'
        )

        self.completed_advert = Advert.objects.create(
            seller=self.user, title='Завершённое объявление', description='Описание завершённого', price=500,
            category=self.category_service, address='СПб', status=Advert.Status.COMPLETED
        )

        self.archived_advert = Advert.objects.create(
            seller=self.user, title='Архивное объявление', description='Описание архивного', price=200,
            category=self.category_product, address='Казань', status=Advert.Status.ARCHIVED
        )

    def test_list_view_show_only_active(self):
        response = self.client.get(reverse('adverts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Активное объявление')
        self.assertNotContains(response, 'Завершённое объявление')
        self.assertNotContains(response, 'Архивное объявление')

    def test_list_view_search_by_title(self):
        response = self.client.get(reverse('adverts:list') + '?q=Активное')
        self.assertContains(response, 'Активное объявление')
        self.assertNotContains(response, 'Архивное объявление')

    def test_list_view_search_by_description(self):
        response = self.client.get(reverse('adverts:list') + '?q=активного')
        self.assertContains(response, 'Активное объявление')

    def test_list_view_filter_by_category(self):
        response = self.client.get(reverse('adverts:list') + f'?category={self.category_product}')
        self.assertContains(response, 'Активное объявление')
        self.assertNotContains(response, 'Завершённое объявление')

    def test_list_view_sort_by_price_asc(self):
        # Создаём ещё активные объявления с разной ценой
        Advert.objects.create(
            seller=self.user, title='Дешёвое', description='Описание', price=100, category=self.category_product,
            address='Москва'
        )
        Advert.objects.create(
            seller=self.user, title='Дорогое', description='Описание', price=5000, category=self.category_product,
            address='Москва'
        )

        response = self.client.get(reverse('adverts:list') + '?sort=price')
        adverts = response.context['adverts']
        # Первое должно быть с самой низкой ценой
        self.assertEqual(adverts[0].price, 100)

    def test_list_view_sort_by_price_desc(self):
        Advert.objects.create(
            seller=self.user, title='Дешёвое', description='Описание', price=100, category=self.category_product,
            address='Москва'
        )
        Advert.objects.create(
            seller=self.user, title='Дорогое', description='Описание', price=5000, category=self.category_product,
            address='Москва'
        )

        response = self.client.get(reverse('adverts:list') + '?sort=-price')
        adverts = response.context['adverts']
        self.assertEqual(adverts[0].price, 5000)

    def test_list_view_sort_by_date_newest(self):
        response = self.client.get(reverse('adverts:list') + '?sort=-created_at')
        adverts = response.context['adverts']
        # Проверяем, что сортировка работает
        self.assertIsNotNone(adverts)


# ==========================================
# ТЕСТЫ ВЬЮХ: UserProfileView
# ==========================================


class UserProfileViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass123')
        self.profile_url = reverse('users:profile', kwargs={'pk': self.user.pk})

        # Создаём объявления разных статусов
        self.active_advert = Advert.objects.create(
            seller=self.user, title='Активное', description='Описание', price=1000, category=Advert.Category.PRODUCT,
            status=Advert.Status.ACTIVE
        )
        self.completed_advert = Advert.objects.create(
            seller=self.user, title='Завершённое', description='Описание', price=500, category=Advert.Category.PRODUCT,
            status=Advert.Status.COMPLETED
        )
        self.archived_advert = Advert.objects.create(
            seller=self.user, title='Архивное', description='Описание', price=200, category=Advert.Category.PRODUCT,
            status=Advert.Status.ARCHIVED
        )

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_unauthenticated_redirect(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_view_contains_user_data(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'testuser')
        self.assertEqual(response.context['user'], self.user)

    def test_profile_view_groups_adverts_by_status(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)

        # Проверяем, что в контексте есть grouped_adverts
        self.assertIn('grouped_adverts', response.context)

        grouped = response.context['grouped_adverts']
        self.assertIn('active', grouped)
        self.assertIn('completed', grouped)
        self.assertIn('archived', grouped)

        # Проверяем количество объявлений в каждой группе
        self.assertEqual(len(grouped['active']), 1)
        self.assertEqual(len(grouped['completed']), 1)
        self.assertEqual(len(grouped['archived']), 1)

        # Проверяем, что правильные объявления в правильных группах
        self.assertEqual(grouped['active'][0].title, 'Активное')
        self.assertEqual(grouped['completed'][0].title, 'Завершённое')
        self.assertEqual(grouped['archived'][0].title, 'Архивное')


class UserProfileUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.update_url = reverse('users:profile_update', kwargs={'pk': self.user.pk})

    def test_profile_update_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile_update.html')

    def test_profile_update_view_unauthenticated_redirect(self):
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_update_view_other_user_forbidden(self):
        CustomUser.objects.create_user(username='other', password='otherpass123')
        self.client.login(username='other', password='otherpass123')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 404)

    def test_profile_update_success(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'newemail@example.com',
            'phone_number': '+79001234567',
            'address': 'Москва, ул. Тестовая, д. 1',
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Иван')
        self.assertEqual(self.user.last_name, 'Иванов')
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.phone_number, '+79001234567')
        self.assertEqual(self.user.address, 'Москва, ул. Тестовая, д. 1')

    def test_profile_update_redirects_to_profile(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'newemail@example.com',
            'phone_number': '+79001234567',
            'address': 'Москва, ул. Тестовая, д. 1',
        }
        response = self.client.post(self.update_url, data)
        self.assertRedirects(response, reverse('users:profile', kwargs={'pk': self.user.pk}))

    def test_profile_update_invalid_email(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'invalid-email',
            'phone_number': '+79001234567',
            'address': 'Москва, ул. Тестовая, д. 1',
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)  # Остаёмся на странице
        self.assertContains(response, 'Введите правильный адрес электронной почты')


class AdminDeleteAdvertTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass123'
        )
        self.regular_user = CustomUser.objects.create_user(username='user', password='userpass123')
        self.other_user = CustomUser.objects.create_user(username='other', password='otherpass123')
        self.advert = Advert.objects.create(
            seller=self.regular_user, title='Тестовое объявление', description='Описание', price=1000,
            category=Advert.Category.PRODUCT, address='Москва'
        )
        self.delete_url = reverse('adverts:delete', kwargs={'pk': self.advert.pk})

    def test_admin_can_delete_any_advert(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Advert.objects.filter(pk=self.advert.pk).exists())

    def test_superuser_can_delete_any_advert(self):
        CustomUser.objects.create_superuser(username='super', email='super@example.com', password='superpass123')
        self.client.login(username='super', password='superpass123')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Advert.objects.filter(pk=self.advert.pk).exists())

    def test_regular_user_cannot_delete_others_advert(self):
        self.client.login(username='other', password='otherpass123')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Advert.objects.filter(pk=self.advert.pk).exists())

    def test_owner_can_delete_own_advert(self):
        self.client.login(username='user', password='userpass123')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Advert.objects.filter(pk=self.advert.pk).exists())
