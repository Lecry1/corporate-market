from adverts.models import Advert
from django.test import TestCase
from reviews.models import Review
from users.models import CustomUser


class ReviewModelTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='review_seller')
        self.buyer = CustomUser.objects.create_user(username='review_buyer')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Урок английского',
            description='Индивидуальный урок английского языка.',
            category=Advert.Category.SERVICE,
            status=Advert.Status.COMPLETED,
        )

    def test_review_creation_and_string_representation(self):
        review = Review.objects.create(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=5,
            comment='Всё прошло отлично.',
        )

        expected = 'Отзыв от review_buyer на review_seller (Рейтинг: 5)'
        self.assertEqual(str(review), expected)
        self.assertEqual(review.to_user, self.seller)
        self.assertEqual(review.advert, self.advert)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
