from django.urls import path
from reviews.views import AdvertReviewListView, ReviewCreateView, UserReviewListView

app_name = 'reviews'

urlpatterns = [
    path('chats/<int:chat_pk>/create/', ReviewCreateView.as_view(), name='create'),
    path('users/<int:user_pk>/', UserReviewListView.as_view(), name='user-list'),
    path('adverts/<int:advert_pk>/', AdvertReviewListView.as_view(), name='advert-list'),
]
