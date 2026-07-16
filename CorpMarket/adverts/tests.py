import shutil
import tempfile
from io import BytesIO

from PIL import Image

from adverts.models import Advert, Photo
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


User = get_user_model()

TEST_MEDIA_ROOT = tempfile.mkdtemp()


def tearDownModule():
    """
    Удаляет временные изображения после завершения тестов модуля.
    """

    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


def create_test_image(
    filename="test.jpg",
    image_format="JPEG",
):
    """
    Создаёт корректное изображение в памяти.

    Файл не требуется хранить в репозитории.
    """

    image_data = BytesIO()

    Image.new(
        "RGB",
        (100, 100),
        color="white",
    ).save(
        image_data,
        format=image_format,
    )

    image_data.seek(0)

    content_type_by_format = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    return SimpleUploadedFile(
        filename,
        image_data.read(),
        content_type=content_type_by_format[image_format],
    )


def create_invalid_image(filename="broken.txt"):
    """
    Создаёт файл, который не является изображением.
    """

    return SimpleUploadedFile(
        filename,
        b"this is not an image",
        content_type="text/plain",
    )


def create_advert(
    seller,
    *,
    title="Тестовое объявление",
    description="Тестовое описание",
    price=1000,
    category=Advert.Category.PRODUCT,
    status=Advert.Status.ACTIVE,
    address="Москва",
):
    """
    Создаёт объявление для тестов.
    """

    return Advert.objects.create(
        seller=seller,
        title=title,
        description=description,
        price=price,
        category=category,
        status=status,
        address=address,
    )


def create_photo(
    advert,
    *,
    filename="existing.jpg",
):
    """
    Создаёт фотографию для существующего объявления.
    """

    return Photo.objects.create(
        advert=advert,
        image=create_test_image(filename),
    )


def create_formset_management_data(
    *,
    total_forms,
    initial_forms,
):
    """
    Возвращает обязательные management-поля photo formset.
    """

    return {
        "photos-TOTAL_FORMS": str(total_forms),
        "photos-INITIAL_FORMS": str(initial_forms),
        "photos-MIN_NUM_FORMS": "1",
        "photos-MAX_NUM_FORMS": "5",
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdvertModelTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller",
        )

    def test_advert_creation_and_string_representation(self):
        advert = create_advert(
            self.seller,
            title="Велосипед",
            description=(
                "Городской велосипед в хорошем состоянии."
            ),
            price=25000,
            address="Москва",
        )

        self.assertEqual(
            str(advert),
            "Велосипед",
        )
        self.assertEqual(
            advert.status,
            Advert.Status.ACTIVE,
        )
        self.assertEqual(
            advert.get_absolute_url(),
            reverse(
                "adverts:detail",
                kwargs={"pk": advert.pk},
            ),
        )
        self.assertTrue(
            Advert.objects.filter(pk=advert.pk).exists()
        )

    def test_main_photo_returns_first_photo(self):
        advert = create_advert(self.seller)

        first_photo = create_photo(
            advert,
            filename="first.jpg",
        )
        create_photo(
            advert,
            filename="second.jpg",
        )

        self.assertEqual(
            advert.main_photo,
            first_photo,
        )

    def test_price_is_negotiable_when_price_is_empty(self):
        advert = create_advert(
            self.seller,
            price=None,
        )

        self.assertTrue(advert.is_price_negotiable)

    def test_price_is_not_negotiable_when_price_is_set(self):
        advert = create_advert(
            self.seller,
            price=5000,
        )

        self.assertFalse(advert.is_price_negotiable)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdvertViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.advert = create_advert(
            self.user,
            title="Тестовое объявление",
            description="Тестовое описание",
        )

        create_photo(self.advert)

    def test_advert_list_view_status_code(self):
        response = self.client.get(
            reverse("adverts:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "adverts/advert_list.html",
        )

    def test_advert_list_contains_advert(self):
        response = self.client.get(
            reverse("adverts:list")
        )

        self.assertContains(
            response,
            "Тестовое объявление",
        )

    def test_advert_detail_view_status_code(self):
        response = self.client.get(
            reverse(
                "adverts:detail",
                args=[self.advert.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "adverts/advert_detail.html",
        )

    def test_advert_detail_contains_advert(self):
        response = self.client.get(
            reverse(
                "adverts:detail",
                args=[self.advert.pk],
            )
        )

        self.assertContains(
            response,
            "Тестовое объявление",
        )
        self.assertContains(
            response,
            "Тестовое описание",
        )

    def test_advert_detail_not_found(self):
        response = self.client.get(
            reverse(
                "adverts:detail",
                args=[999999],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdvertCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.create_url = reverse("adverts:create")

    def login(self):
        self.client.login(
            username="testuser",
            password="testpass123",
        )

    def valid_advert_data(self):
        return {
            "title": "Новое объявление",
            "description": "Описание нового объявления",
            "price": 2000,
            "category": Advert.Category.SERVICE,
            "address": "Москва",
        }

    def test_create_view_redirect_if_not_logged_in(self):
        response = self.client.get(self.create_url)

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_create_view_logged_in(self):
        self.login()

        response = self.client.get(self.create_url)

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "adverts/advert_form.html",
        )

    def test_create_advert_success_with_one_photo(self):
        self.login()

        data = self.valid_advert_data()
        data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        data["photos-0-image"] = create_test_image(
            "advert.jpg"
        )

        response = self.client.post(
            self.create_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        advert = Advert.objects.get(
            title="Новое объявление"
        )

        self.assertEqual(
            advert.seller,
            self.user,
        )
        self.assertEqual(
            advert.photos.count(),
            1,
        )
        self.assertEqual(
            Photo.objects.count(),
            1,
        )

    def test_create_advert_requires_photo(self):
        self.login()

        data = self.valid_advert_data()
        data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        data["photos-0-image"] = ""

        response = self.client.post(
            self.create_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertFalse(
            Advert.objects.filter(
                title="Новое объявление",
            ).exists()
        )
        self.assertEqual(
            Photo.objects.count(),
            0,
        )
        self.assertContains(
            response,
            "Добавьте минимум одну фотографию.",
        )

    def test_invalid_main_form_does_not_save_uploaded_photo(self):
        """
        Если основная форма невалидна, загруженное изображение
        не должно сохраняться отдельно.
        """

        self.login()

        data = self.valid_advert_data()
        data["title"] = ""
        data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        data["photos-0-image"] = create_test_image(
            "first-attempt.jpg"
        )

        response = self.client.post(
            self.create_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            Advert.objects.count(),
            0,
        )
        self.assertEqual(
            Photo.objects.count(),
            0,
        )

    def test_resubmit_after_invalid_form_creates_only_one_photo(self):
        """
        Воспроизводит старый баг:

        1. Пользователь отправляет невалидную форму с фотографией.
        2. Затем исправляет форму и выбирает новую фотографию.
        3. В объявлении должна оказаться только новая фотография,
           без дублей.
        """

        self.login()

        invalid_data = self.valid_advert_data()
        invalid_data["title"] = ""
        invalid_data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        invalid_data["photos-0-image"] = create_test_image(
            "first-attempt.jpg"
        )

        invalid_response = self.client.post(
            self.create_url,
            invalid_data,
        )

        self.assertEqual(
            invalid_response.status_code,
            200,
        )
        self.assertEqual(
            Advert.objects.count(),
            0,
        )
        self.assertEqual(
            Photo.objects.count(),
            0,
        )

        valid_data = self.valid_advert_data()
        valid_data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        valid_data["photos-0-image"] = create_test_image(
            "second-attempt.jpg"
        )

        valid_response = self.client.post(
            self.create_url,
            valid_data,
        )

        self.assertEqual(
            valid_response.status_code,
            302,
        )

        advert = Advert.objects.get(
            title="Новое объявление"
        )

        self.assertEqual(
            advert.photos.count(),
            1,
        )
        self.assertEqual(
            Photo.objects.count(),
            1,
        )

    def test_invalid_image_does_not_create_advert(self):
        self.login()

        data = self.valid_advert_data()
        data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=0,
            )
        )
        data["photos-0-image"] = create_invalid_image()

        response = self.client.post(
            self.create_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertFalse(
            Advert.objects.filter(
                title="Новое объявление",
            ).exists()
        )
        self.assertEqual(
            Photo.objects.count(),
            0,
        )

    def test_create_advert_with_two_photos_saves_each_once(self):
        self.login()

        data = self.valid_advert_data()
        data.update(
            create_formset_management_data(
                total_forms=2,
                initial_forms=0,
            )
        )
        data["photos-0-image"] = create_test_image(
            "first.jpg"
        )
        data["photos-1-image"] = create_test_image(
            "second.jpg"
        )

        response = self.client.post(
            self.create_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        advert = Advert.objects.get(
            title="Новое объявление"
        )

        self.assertEqual(
            advert.photos.count(),
            2,
        )

        self.assertEqual(
            list(
                advert.photos.values_list(
                    "order",
                    flat=True,
                )
            ),
            [0, 1],
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdvertUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
        )

        self.advert = create_advert(
            self.user,
            title="Тестовое объявление",
            description="Тестовое описание",
            price=1000,
            address="Москва",
        )

        self.photo = create_photo(
            self.advert,
            filename="existing.jpg",
        )

        self.update_url = reverse(
            "adverts:update",
            args=[self.advert.pk],
        )

    def login_as_owner(self):
        self.client.login(
            username="testuser",
            password="testpass123",
        )

    def valid_update_data(self):
        data = {
            "title": "Обновлённое объявление",
            "description": "Обновлённое описание",
            "price": 3000,
            "category": Advert.Category.SERVICE,
            "address": "Санкт-Петербург",
            "status": Advert.Status.ACTIVE,
            "photos-0-id": str(self.photo.pk),
        }

        data.update(
            create_formset_management_data(
                total_forms=1,
                initial_forms=1,
            )
        )

        return data

    def test_update_view_redirect_if_not_logged_in(self):
        response = self.client.get(self.update_url)

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_update_view_other_user_forbidden(self):
        self.client.login(
            username="otheruser",
            password="otherpass123",
        )

        response = self.client.get(self.update_url)

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_update_advert_success_preserves_existing_photo(self):
        self.login_as_owner()

        response = self.client.post(
            self.update_url,
            self.valid_update_data(),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.advert.refresh_from_db()

        self.assertEqual(
            self.advert.title,
            "Обновлённое объявление",
        )
        self.assertEqual(
            self.advert.description,
            "Обновлённое описание",
        )
        self.assertEqual(
            self.advert.price,
            3000,
        )
        self.assertEqual(
            self.advert.photos.count(),
            1,
        )
        self.assertTrue(
            self.advert.photos.filter(
                pk=self.photo.pk,
            ).exists()
        )

    def test_update_can_add_new_photo(self):
        self.login_as_owner()

        data = self.valid_update_data()
        data.update(
            create_formset_management_data(
                total_forms=2,
                initial_forms=1,
            )
        )
        data["photos-1-image"] = create_test_image(
            "new.jpg"
        )

        response = self.client.post(
            self.update_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.advert.refresh_from_db()

        self.assertEqual(
            self.advert.photos.count(),
            2,
        )

    def test_invalid_new_photo_does_not_save_text_changes(self):
        """
        Если новая фотография невалидна, изменение описания
        и остальных полей объявления не должно сохраняться.
        """

        self.login_as_owner()

        original_title = self.advert.title
        original_description = self.advert.description
        original_price = self.advert.price
        original_photo_count = self.advert.photos.count()

        data = self.valid_update_data()
        data.update(
            create_formset_management_data(
                total_forms=2,
                initial_forms=1,
            )
        )
        data["description"] = (
            "Это описание не должно сохраниться"
        )
        data["price"] = 999999
        data["photos-1-image"] = create_invalid_image()

        response = self.client.post(
            self.update_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.advert.refresh_from_db()

        self.assertEqual(
            self.advert.title,
            original_title,
        )
        self.assertEqual(
            self.advert.description,
            original_description,
        )
        self.assertEqual(
            self.advert.price,
            original_price,
        )
        self.assertEqual(
            self.advert.photos.count(),
            original_photo_count,
        )

    def test_cannot_delete_last_photo_without_replacement(self):
        self.login_as_owner()

        data = self.valid_update_data()
        data["photos-0-DELETE"] = "on"

        response = self.client.post(
            self.update_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.advert.refresh_from_db()

        self.assertTrue(
            self.advert.photos.filter(
                pk=self.photo.pk,
            ).exists()
        )
        self.assertContains(
            response,
            "Добавьте минимум одну фотографию.",
        )

    def test_can_replace_last_photo(self):
        self.login_as_owner()

        data = self.valid_update_data()
        data.update(
            create_formset_management_data(
                total_forms=2,
                initial_forms=1,
            )
        )
        data["photos-0-DELETE"] = "on"
        data["photos-1-image"] = create_test_image(
            "replacement.jpg"
        )

        response = self.client.post(
            self.update_url,
            data,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.advert.refresh_from_db()

        self.assertEqual(
            self.advert.photos.count(),
            1,
        )
        self.assertFalse(
            Photo.objects.filter(
                pk=self.photo.pk,
            ).exists()
        )

    def test_superuser_can_update_other_users_advert(self):
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

        self.client.login(
            username="admin",
            password="adminpass123",
        )

        response = self.client.post(
            self.update_url,
            self.valid_update_data(),
        )

        self.assertEqual(
            response.status_code,
            302,
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AdvertDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
        )

        self.advert = create_advert(
            self.user,
        )
        create_photo(self.advert)

        self.delete_url = reverse(
            "adverts:delete",
            args=[self.advert.pk],
        )

    def test_delete_view_redirect_if_not_logged_in(self):
        response = self.client.get(self.delete_url)

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_delete_view_other_user_forbidden(self):
        self.client.login(
            username="otheruser",
            password="otherpass123",
        )

        response = self.client.get(self.delete_url)

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_delete_advert_success(self):
        self.client.login(
            username="testuser",
            password="testpass123",
        )

        advert_pk = self.advert.pk

        response = self.client.post(
            self.delete_url,
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertFalse(
            Advert.objects.filter(
                pk=advert_pk,
            ).exists()
        )
        self.assertEqual(
            Photo.objects.count(),
            0,
        )

    def test_superuser_can_delete_other_users_advert(self):
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

        self.client.login(
            username=superuser.username,
            password="adminpass123",
        )

        advert_pk = self.advert.pk

        response = self.client.post(
            self.delete_url,
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertFalse(
            Advert.objects.filter(
                pk=advert_pk,
            ).exists()
        )
