from django.contrib import admin
from photos.models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'advert', 'caption', 'order', 'uploaded_at')
    list_filter = ('uploaded_at', )
    search_fields = ('advert__title', 'caption')
    list_select_related = ('advert', )
