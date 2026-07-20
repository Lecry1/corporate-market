from django.contrib import admin
from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user', 'advert', 'flag', 'rating', 'created_at')
    list_filter = ('flag', 'rating', 'created_at')
    search_fields = ('comment', 'from_user__username', 'to_user__username', 'advert__title')
    list_select_related = ('from_user', 'to_user', 'advert')
