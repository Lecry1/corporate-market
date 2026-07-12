from adverts.models import Advert
from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser


class AdvertModelTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='seller')

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
