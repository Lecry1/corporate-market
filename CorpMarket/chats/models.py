from django.conf import settings
from django.db import models


class Chat(models.Model):
    """Чат между пользователями по объявлению"""

    advert = models.ForeignKey(
        'adverts.Advert', on_delete=models.CASCADE, related_name="chats", verbose_name="Объявление"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_chats", verbose_name="Покупатель"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_chats", verbose_name="Продавец"
    )
    is_active = models.BooleanField(default=True, verbose_name="Чат активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ["-updated_at"]
        unique_together = [["advert", "buyer", "seller"]]
        indexes = [
            models.Index(fields=["advert", "is_active"]),
            models.Index(fields=["buyer", "is_active"]),
            models.Index(fields=["seller", "is_active"]),
        ]

    def __str__(self):
        return f"Чат по '{self.advert.title}' между {self.buyer} и {self.seller}"

    @property
    def last_message(self):
        return self.messages.first()

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def mark_as_read(self, user):
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    def get_other_user(self, user):
        if self.buyer == user:
            return self.seller
        elif self.seller == user:
            return self.buyer
        return None
