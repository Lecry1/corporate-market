from django.db.models.signals import post_delete
from django.dispatch import receiver
from reviews.models import Review


@receiver(post_delete, sender=Review)
def update_rating_after_review_delete(sender, instance, **kwargs):
    sender._update_user_rating(user_id=instance.to_user_id, flag=instance.flag)
