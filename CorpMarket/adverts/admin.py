from django.contrib import admin

from .models import Advert, Photo


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    fields = ("image", "caption", "order")


@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "category", "status", "created_at")
    list_filter = ("category", "status", "created_at")
    search_fields = ("title", "description", "seller__username")
    inlines = [PhotoInline]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("advert", "order", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("advert__title", "caption")
