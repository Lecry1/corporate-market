from django.conf import settings
from django.db import models


class Chat(models.Model):

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


class Message(models.Model):

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages", verbose_name="Чат")

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages", verbose_name="Отправитель"
    )

    text = models.TextField(verbose_name="Текст сообщения")

    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["chat", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"Сообщение от {self.sender} в чате {self.chat.id}"

    def get_preview(self, length=50):
        if len(self.text) <= length:
            return self.text
        return f"{self.text[:length]}..."

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def mark_as_unread(self):
        self.is_read = False
        self.save()
