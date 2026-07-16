from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from chats.models import Chat, Message
from adverts.models import Advert
from reviews.forms import ReviewForm
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
        # Чат нужен для проверки рейтинга и flow-тестов
        self.chat = Chat.objects.create(advert=self.advert, buyer=self.buyer, seller=self.seller)
        Message.objects.create(
            chat=self.chat,
            sender=self.buyer,
            text="Здравствуйте, объявление актуально?",
        )
        Message.objects.create(
            chat=self.chat,
            sender=self.seller,
            text="Здравствуйте, да, актуально.",
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

        # Добавлено из dev: проверка автоматического пересчета рейтинга
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.seller_rating, 5.0)

        review.delete()
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.seller_rating, 0.0)

    def test_review_is_invalid_without_two_way_communication(self):
        self.chat.messages.all().delete()

        Message.objects.create(chat=self.chat,sender=self.buyer,text="Сообщение покупателя без ответа продавца.")

        review = Review(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=1,
            comment="Попытка оставить отзыв без общения.",
        )

        with self.assertRaises(ValidationError):
            review.full_clean()


# ==========================================
# ТЕСТЫ ФОРМ (из ветки dev)
# ==========================================

class ReviewFormTest(TestCase):

    def test_rating_from_one_to_five_is_valid(self):
        form = ReviewForm(data={'rating': 5, 'comment': ''})
        self.assertTrue(form.is_valid())

    def test_rating_outside_allowed_range_is_invalid(self):
        form = ReviewForm(data={'rating': 6, 'comment': 'Неверная оценка'})
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)


# ==========================================
# ТЕСТЫ БИЗНЕС-ЛОГИКИ И ВЬЮХ
# ==========================================

class ReviewFlowTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='seller', password='safe-password')
        self.buyer = CustomUser.objects.create_user(username='buyer', password='safe-password')
        self.outsider = CustomUser.objects.create_user(username='outsider', password='safe-password')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title="Активное объявление",
            description="Объявление для проверки отзывов.",
            category=Advert.Category.PRODUCT,
            status=Advert.Status.ACTIVE,
        )
        self.chat = Chat.objects.create(advert=self.advert, buyer=self.buyer, seller=self.seller)
        Message.objects.create(
            chat=self.chat,
            sender=self.buyer,
            text="Здравствуйте, можно уточнить детали?",
        )
        Message.objects.create(
            chat=self.chat,
            sender=self.seller,
            text="Здравствуйте, конечно.",
        )

    def test_guest_is_redirected_to_login(self):
        url = reverse('reviews:create', kwargs={'chat_pk': self.chat.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f'{reverse("users:login")}?next={url}')

    def test_buyer_can_review_seller(self):
        self.client.force_login(self.buyer)
        # Примечание: мы намеренно передаем "левые" from_user/to_user/flag,
        # чтобы проверить, что вьюха игнорирует их и ставит правильные (защита от подделки)
        response = self.client.post(
            reverse('reviews:create', kwargs={'chat_pk': self.chat.pk}),
            {
                'rating': 4,
                'comment': 'Хорошая сделка.',
                'from_user': self.outsider.pk,
                'to_user': self.outsider.pk,
                'flag': Review.Flag.TO_BUYER,
            },
        )

        review = Review.objects.get()
        self.assertRedirects(response, reverse('chats:detail', kwargs={'pk': self.chat.pk}))
        self.assertEqual(review.from_user, self.buyer)
        self.assertEqual(review.to_user, self.seller)
        self.assertEqual(review.advert, self.advert)
        self.assertEqual(review.flag, Review.Flag.TO_SELLER)

    def test_seller_can_review_buyer(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse('reviews:create', kwargs={'chat_pk': self.chat.pk}),
            {
                'rating': 5,
                'comment': 'Ответственный покупатель.'
            },
        )

        review = Review.objects.get()
        self.assertRedirects(response, reverse('chats:detail', kwargs={'pk': self.chat.pk}))
        self.assertEqual(review.to_user, self.buyer)
        self.assertEqual(review.flag, Review.Flag.TO_BUYER)

    def test_review_form_is_available_for_active_advert(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("reviews:create",kwargs={"chat_pk": self.chat.pk},))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,"reviews/review_form.html",)

    def test_outsider_cannot_review_chat_participant(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse('reviews:create', kwargs={'chat_pk': self.chat.pk}))
        self.assertEqual(response.status_code, 404)

    def test_duplicate_review_is_not_created(self):
        Review.objects.create(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=5,
        )
        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse('reviews:create', kwargs={'chat_pk': self.chat.pk}),
            {
                'rating': 1,
                'comment': 'Повторный отзыв'
            },
        )

        self.assertRedirects(response, reverse('chats:detail', kwargs={'pk': self.chat.pk}))
        self.assertEqual(Review.objects.count(), 1)

    def test_review_lists_are_public(self):
        review = Review.objects.create(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=5,
            comment='Публичный отзыв',
        )

        user_response = self.client.get(reverse('reviews:user-list', kwargs={'user_pk': self.seller.pk}))
        advert_response = self.client.get(reverse('reviews:advert-list', kwargs={'advert_pk': self.advert.pk}))

        self.assertEqual(user_response.status_code, 200)
        self.assertEqual(advert_response.status_code, 200)
        self.assertContains(user_response, review.comment)
        self.assertContains(advert_response, review.comment)

    def test_active_chat_shows_review_action(self):
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("chats:detail",kwargs={"pk": self.chat.pk},))

        self.assertTrue(response.context["can_leave_review"])
        self.assertContains(response,reverse("reviews:create",kwargs={"chat_pk": self.chat.pk},),)

    def test_review_action_is_hidden_after_review(self):
        Review.objects.create(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=5,
            comment="Отзыв уже оставлен.",
        )

        self.client.force_login(self.buyer)

        response = self.client.get(reverse("chats:detail",kwargs={"pk": self.chat.pk},))

        self.assertFalse(response.context["can_leave_review"])
        self.assertTrue(response.context["review_exists"])
        self.assertNotContains(response,reverse("reviews:create",kwargs={"chat_pk": self.chat.pk},),)

    def test_review_can_be_created_for_active_advert(self):
        self.advert.status = Advert.Status.ACTIVE
        self.advert.save(update_fields=["status"])

        review = Review(
            from_user=self.buyer,
            to_user=self.seller,
            advert=self.advert,
            flag=Review.Flag.TO_SELLER,
            rating=5,
            comment="Отзыв по активному объявлению.",
        )

        review.full_clean()
        review.save()

        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

    def test_review_is_unavailable_without_seller_reply(self):
        self.chat.messages.all().delete()

        Message.objects.create(chat=self.chat,sender=self.buyer,text="Здравствуйте, объявление актуально?")
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("reviews:create",kwargs={"chat_pk": self.chat.pk}))
        self.assertRedirects(response,reverse("chats:detail",kwargs={"pk": self.chat.pk},))

        self.assertFalse(Review.objects.exists())

    def test_review_action_is_hidden_without_seller_reply(self):
        self.chat.messages.all().delete()

        Message.objects.create(chat=self.chat,sender=self.buyer,text="Первое сообщение покупателя.")
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("chats:detail",kwargs={"pk": self.chat.pk}))

        self.assertFalse(response.context["can_leave_review"])
        self.assertFalse(response.context["has_two_way_communication"])
        self.assertNotContains(response,reverse("reviews:create",kwargs={"chat_pk": self.chat.pk}))

    def test_review_action_appears_after_seller_reply(self):
        self.chat.messages.all().delete()
        Message.objects.create(chat=self.chat,sender=self.buyer,text="Здравствуйте, объявление актуально?")

        self.client.force_login(self.buyer)

        response_before_reply = self.client.get(reverse("chats:detail",kwargs={"pk": self.chat.pk}))
        self.assertFalse(response_before_reply.context["can_leave_review"])

        Message.objects.create(chat=self.chat,sender=self.seller,text="Здравствуйте, да, актуально.")
        response_after_reply = self.client.get(reverse("chats:detail",kwargs={"pk": self.chat.pk}))

        self.assertTrue(response_after_reply.context["has_two_way_communication"])
        self.assertTrue(response_after_reply.context["can_leave_review"])
        self.assertContains(response_after_reply,reverse("reviews:create",kwargs={"chat_pk": self.chat.pk}))
