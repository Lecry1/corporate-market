from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):

    class Flag(models.TextChoices):
        TO_BUYER = "to_buyer", "Покупателю"
        TO_SELLER = "to_seller", "Продавцу"

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

        unique_together = [["from_user", "advert"]]
        indexes = [
            models.Index(fields=["to_user", "-created_at"]),
            models.Index(fields=["advert", "-created_at"]),
        ]

    def __str__(self):
        return f"Отзыв от {self.from_user} на {self.to_user} (Рейтинг: {self.rating})"

    """
    @property
    def is_positive(self):
        return self.rating >= 4

    @property
    def is_negative(self):
        return self.rating <= 2

    @property
    def is_neutral(self):
        return self.rating == 3
    """

    def get_summary(self):
        """Краткое описание отзыва для уведомлений"""
        flag_text = self.get_flag_display()

        comment_part = self.comment[:50] if self.comment else ""
        return f"{flag_text} | Рейтинг: {self.rating} | {comment_part}..."
