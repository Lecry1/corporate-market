from chats.views import ChatDetailView, ChatListView, StartChatView
from django.urls import path

app_name = 'chats'

urlpatterns = [
    path('', ChatListView.as_view(), name='list'),
    path('start/<int:advert_pk>/', StartChatView.as_view(), name='start'),
    path('<int:pk>/', ChatDetailView.as_view(), name='detail'),
]
