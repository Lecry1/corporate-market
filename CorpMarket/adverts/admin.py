from adverts.models import Advert, Photo
from django.contrib import admin


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    fields = ("image", "caption", "order")


@admin.register(Advert)
class AdvertAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "category", "status", "price", "created_at")
    list_filter = ("category", "status", "created_at")
    search_fields = ("title", "description", "address", "seller__username")
    list_select_related = ("seller",)
    date_hierarchy = "created_at"
    inlines = [PhotoInline]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("advert", "order", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("advert__title", "caption")
