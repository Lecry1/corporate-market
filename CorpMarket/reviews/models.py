from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Q


class Review(models.Model):

    class Flag(models.TextChoices):
        TO_BUYER = "to_buyer", "От продавца"
        TO_SELLER = "to_seller", "От покупателя"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_left",
        verbose_name="От кого (автор отзыва)"
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received",
        verbose_name="Кому (получатель отзыва)"
    )

    advert = models.ForeignKey(
        "adverts.Advert", on_delete=models.CASCADE, related_name="reviews", verbose_name="Объявление"
    )

    flag = models.CharField(max_length=20, choices=Flag.choices, verbose_name="Кому адресован")

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Рейтинг"
    )

    comment = models.TextField(blank=True, verbose_name="Комментарий")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=['from_user', 'advert', 'to_user'],
                name='unique_review_participants_per_advert',
            ),
        ]
        indexes = [
            models.Index(fields=["to_user", "-created_at"]),
            models.Index(fields=["advert", "-created_at"]),
        ]

    def __str__(self):
        return f"Отзыв от {self.from_user} на {self.to_user} (Рейтинг: {self.rating})"

    def clean(self):
        errors = {}

        if self.from_user_id and self.to_user_id and self.from_user_id == self.to_user_id:
            errors['to_user'] = 'Нельзя оставить отзыв самому себе.'

        if self.advert_id and self.advert.status != self.advert.Status.COMPLETED:
            errors['advert'] = 'Отзыв можно оставить только после завершения сделки.'

        if self.from_user_id and self.to_user_id and self.advert_id:
            from chats.models import Chat

            shared_chat_exists = Chat.objects.filter(advert_id=self.advert_id).filter(
                Q(buyer_id=self.from_user_id, seller_id=self.to_user_id)
                | Q(seller_id=self.from_user_id, buyer_id=self.to_user_id)
            ).exists()

            if not shared_chat_exists:
                errors['to_user'] = 'Отзыв можно оставить только участнику чата по объявлению.'

            expected_flag = self.Flag.TO_SELLER if self.to_user_id == self.advert.seller_id else self.Flag.TO_BUYER
            if self.flag != expected_flag:
                errors['flag'] = 'Тип отзыва не соответствует роли получателя.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        previous_recipient = None

        if self.pk:
            previous_recipient = type(self).objects.filter(pk=self.pk).values('to_user_id', 'flag').first()

        self.full_clean()
        result = super().save(*args, **kwargs)

        self._update_user_rating(user_id=self.to_user_id, flag=self.flag)

        if previous_recipient and (
            previous_recipient['to_user_id'] != self.to_user_id or previous_recipient['flag'] != self.flag
        ):
            self._update_user_rating(
                user_id=previous_recipient['to_user_id'],
                flag=previous_recipient['flag'],
            )

        return result

    @classmethod
    def _update_user_rating(cls, user_id, flag):
        average_rating = cls.objects.filter(to_user_id=user_id, flag=flag).aggregate(value=Avg('rating'))['value']
        rating_field = 'seller_rating' if flag == cls.Flag.TO_SELLER else 'buyer_rating'
        user_model = get_user_model()
        user_model.objects.filter(pk=user_id).update(**{rating_field: round(average_rating or 0.0, 2)})

    def get_summary(self):
        """Вернуть краткое описание отзыва для уведомлений."""
        flag_text = self.get_flag_display()
        comment_part = self.comment[:50] if self.comment else 'Без комментария'
        return f'{flag_text} | Рейтинг: {self.rating} | {comment_part}'
