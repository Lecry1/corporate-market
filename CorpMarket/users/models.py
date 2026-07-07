from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    photo = models.ImageField(
        upload_to='users/photos/', 
        blank=True, 
        null=True, 
        verbose_name="Фото профиля"
    )

    address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Адрес"
    )

    buyer_rating = models.FloatField(
        default=0.0, 
        verbose_name="Рейтинг покупателя"
    )

    seller_rating = models.FloatField(
        default=0.0, 
        verbose_name="Рейтинг продавца"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
    
    #TODO: "1+ кастомный метод или property у модели"

