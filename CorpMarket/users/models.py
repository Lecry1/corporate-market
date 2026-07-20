from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class CustomUser(AbstractUser):
    photo = models.ImageField(
        upload_to="users/photos/",
        blank=True,
        null=True,
        verbose_name='Фото профиля',
    )
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес')
    buyer_rating = models.FloatField(default=0.0, verbose_name='Рейтинг покупателя')
    seller_rating = models.FloatField(default=0.0, verbose_name='Рейтинг продавца')

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="users_unique_email_ci",
            ),
        ]

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        full_name = self.get_full_name()
        return full_name or self.username

    @property
    def is_market_admin(self):
        return self.is_superuser or hasattr(self, 'admin_profile')


class Admin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="admin_profile",
        db_column="id_user",
        verbose_name="Пользователь",
    )

    class Meta:
        db_table = "admins"
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"

    def __str__(self):
        return f"Администратор {self.user}"
