from django.db import models

class Reviews(models.Model):
    from_user = models.ForeignKey(
        'Users', 
        on_delete = models.CASCADE, 
        related_name = 'reviews_left'
    )
    
    to_user = models.ForeignKey(
        'Users', 
        on_delete = models.CASCADE, 
        related_name = 'reviews_received'
    )
    
    advert = models.ForeignKey(
        'Adverts', 
        on_delete = models.CASCADE, 
        related_name = 'reviews'
    )

    FLAG_CHOICES = [('to_buyer', 'Покупателю'), ('to_seller', 'Продавцу')]

    flag = models.CharField(max_length = 20, choices = FLAG_CHOICES)

    rating = models.IntegerField()

    comment = models.TextField(blank = True, null = True)

    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Отзыв от {self.from_user} на {self.to_user} (Рейтинг: {self.rating})"