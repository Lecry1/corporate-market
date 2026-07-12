from adverts.models import Advert
from django.contrib import admin


@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'status', 'price', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('title', 'description', 'address', 'seller__username')
    list_select_related = ('seller', )
    date_hierarchy = 'created_at'
