from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone


class Advert(models.Model):

    class Category(models.TextChoices):
        PRODUCT = 'product', 'Товар'
        SERVICE = 'service', 'Услуга'
        EVENT = 'event', 'Мероприятие'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активно'
        COMPLETED = 'completed', 'Выполнено/продано'
        ARCHIVED = 'archived', 'Архивировано'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adverts',
        verbose_name='Продавец',
    )
    title = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Цена')
    category = models.CharField(max_length=20, choices=Category.choices, verbose_name='Категория')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Статус')
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def main_photo(self):
        return self.photos.first()

    def get_absolute_url(self):
        return reverse('adverts:detail', kwargs={'pk': self.pk})

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(days=30)

    @property
    def is_price_negotiable(self):
        return self.price is None

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.save()


class Photo(models.Model):

    advert = models.ForeignKey(Advert, on_delete=models.CASCADE, related_name='photos', verbose_name="Объявление")

    image = models.ImageField(upload_to='advert_photos/%Y/%m/%d/', verbose_name="Изображение")

    caption = models.CharField(max_length=200, blank=True, verbose_name="Подпись к фото")

    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фото"
        verbose_name_plural = "Фотографии"
        ordering = ["order", "uploaded_at"]
        unique_together = [["advert", "order"]]

    def __str__(self):
        return f"Фото {self.order + 1} для {self.advert.title}"

    def save(self, *args, **kwargs):
        if self._state.adding and self.advert_id and self.order == 0:
            last_order = (
                Photo.objects
                .filter(advert_id=self.advert_id)
                .aggregate(max_order=Max("order"))["max_order"]
            )
            if last_order is not None:
                self.order = last_order + 1

        super().save(*args, **kwargs)
