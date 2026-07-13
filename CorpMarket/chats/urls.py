from django.urls import path

from chats.views import (
    ChatDetailView,
    ChatListView,
    ChatMessagesView,
    StartChatView,
)

app_name = "chats"

urlpatterns = [
    path("", ChatListView.as_view(), name="list"),
    path(
        "start/<int:advert_pk>/",
        StartChatView.as_view(),
        name="start",
    ),
    path(
        "<int:pk>/messages/",
        ChatMessagesView.as_view(),
        name="messages",
    ),
    path(
        "<int:pk>/",
        ChatDetailView.as_view(),
        name="detail",
    ),
]
