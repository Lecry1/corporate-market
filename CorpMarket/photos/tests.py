from adverts.models import Advert
from django.test import TestCase
from photos.models import Photo
from users.models import CustomUser


class PhotoModelTest(TestCase):

    def setUp(self):
        seller = CustomUser.objects.create_user(username='photo_seller')
        self.advert = Advert.objects.create(
            seller=seller,
            title='Настольная лампа',
            description='Лампа для рабочего стола.',
            category=Advert.Category.PRODUCT,
        )

    def test_photo_creation_and_string_representation(self):
        photo = Photo.objects.create(
            advert=self.advert,
            image='advert_photos/lamp.jpg',
            caption='Лампа спереди',
        )

        self.assertEqual(str(photo), 'Фото 1 для Настольная лампа')
        self.assertEqual(photo.advert, self.advert)
        self.assertEqual(self.advert.photos.get(), photo)
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())
