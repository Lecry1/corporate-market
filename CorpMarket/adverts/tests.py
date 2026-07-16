from adverts.models import Advert
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

# ==========================================
# ТЕСТЫ МОДЕЛИ
# ==========================================


class AdvertModelTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(username='seller')

    def test_advert_creation_and_string_representation(self):
        advert = Advert.objects.create(
            seller=self.seller,
            title='Велосипед',
            description='Городской велосипед в хорошем состоянии.',
            price=25000,
            category=Advert.Category.PRODUCT,
            address='Москва',
        )

        self.assertEqual(str(advert), 'Велосипед')
        self.assertEqual(advert.status, Advert.Status.ACTIVE)
        self.assertEqual(advert.get_absolute_url(), reverse('adverts:detail', kwargs={'pk': advert.pk}))
        self.assertTrue(Advert.objects.filter(pk=advert.pk).exists())


# ==========================================
# ТЕСТЫ ВЬЮХ
# ==========================================


class AdvertViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.advert = Advert.objects.create(
            title='Тестовое объявление', description='Тестовое описание', price=1000, category=Advert.Category.PRODUCT,
            seller=self.user
        )

    def test_advert_list_view_status_code(self):
        response = self.client.get(reverse('adverts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adverts/advert_list.html')

    def test_advert_list_contains_advert(self):
        response = self.client.get(reverse('adverts:list'))
        self.assertContains(response, 'Тестовое объявление')

    def test_advert_detail_view_status_code(self):
        response = self.client.get(reverse('adverts:detail', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adverts/advert_detail.html')

    def test_advert_detail_contains_advert(self):
        response = self.client.get(reverse('adverts:detail', args=[self.advert.pk]))
        self.assertContains(response, 'Тестовое объявление')
        self.assertContains(response, 'Тестовое описание')

    def test_advert_detail_not_found(self):
        response = self.client.get(reverse('adverts:detail', args=[999]))
        self.assertEqual(response.status_code, 404)


class AdvertCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_create_view_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('adverts:create'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_create_view_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('adverts:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adverts/advert_form.html')

    def test_create_advert_success(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'title': 'Новое объявление',
            'description': 'Описание нового объявления',
            'price': 2000,
            'category': Advert.Category.SERVICE,
            'address': 'Москва',
            'status': Advert.Status.ACTIVE,
            # 👇 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ PHOTOFORMSET
            'photos-TOTAL_FORMS': '0',
            'photos-INITIAL_FORMS': '0',
            'photos-MIN_NUM_FORMS': '0',
            'photos-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(reverse('adverts:create'), data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Advert.objects.filter(title='Новое объявление').exists())


class AdvertUpdateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass123')
        self.advert = Advert.objects.create(
            title='Тестовое объявление', description='Тестовое описание', price=1000, category=Advert.Category.PRODUCT,
            seller=self.user
        )

    def test_update_view_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('adverts:update', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)

    def test_update_view_other_user_forbidden(self):
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('adverts:update', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 404)

    def test_update_advert_success(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'title': 'Обновлённое объявление',
            'description': 'Обновлённое описание',
            'price': 3000,
            'category': Advert.Category.SERVICE,
            'address': 'Санкт-Петербург',
            'status': Advert.Status.ACTIVE,
            # 👇 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ PHOTOFORMSET
            'photos-TOTAL_FORMS': '0',
            'photos-INITIAL_FORMS': '0',
            'photos-MIN_NUM_FORMS': '0',
            'photos-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(reverse('adverts:update', args=[self.advert.pk]), data)

        self.assertEqual(response.status_code, 302)
        self.advert.refresh_from_db()
        self.assertEqual(self.advert.title, 'Обновлённое объявление')
        self.assertEqual(self.advert.price, 3000)


class AdvertDeleteViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass123')
        self.advert = Advert.objects.create(
            title='Тестовое объявление', description='Тестовое описание', price=1000, category=Advert.Category.PRODUCT,
            seller=self.user
        )

    def test_delete_view_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('adverts:delete', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)

    def test_delete_view_other_user_forbidden(self):
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('adverts:delete', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_advert_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('adverts:delete', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Advert.objects.filter(pk=self.advert.pk).exists())
