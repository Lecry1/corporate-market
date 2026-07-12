from chats.models import Chat, Message
from django.contrib import admin


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'advert', 'seller', 'buyer', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('advert__title', 'seller__username', 'buyer__username')
    list_select_related = ('advert', 'seller', 'buyer')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('text', 'sender__username')
    list_select_related = ('chat', 'sender')
