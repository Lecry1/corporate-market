from django.db import models


class Photo(models.Model):
    """Фотография объявления."""

    advert = models.ForeignKey(
        'adverts.Advert',
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Объявление',
    )
    image = models.ImageField(upload_to='advert_photos/%Y/%m/%d/', verbose_name='Изображение')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Подпись к фото')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок отображения')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фотографии'
        ordering = ['order', 'uploaded_at']
        unique_together = [['advert', 'order']]

    def __str__(self):
        return f'Фото {self.order + 1} для {self.advert.title}'

    def get_image_url(self):
        """Вернуть URL изображения."""
        return self.image.url if self.image else None
