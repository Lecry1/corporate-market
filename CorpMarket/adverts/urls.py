from django.urls import path

from .views import (
    AdvertCreateView,
    AdvertDeleteView,
    AdvertDetailView,
    AdvertListView,
    AdvertUpdateView,
)

app_name = "adverts"

urlpatterns = [
    path("", AdvertListView.as_view(), name="list"),
    path("adverts/create/", AdvertCreateView.as_view(), name="create"),
    path("adverts/<int:pk>/", AdvertDetailView.as_view(), name="detail"),
    path(
        "adverts/<int:pk>/update/",
        AdvertUpdateView.as_view(),
        name="update",
    ),
    path(
        "adverts/<int:pk>/delete/",
        AdvertDeleteView.as_view(),
        name="delete",
    ),
]
