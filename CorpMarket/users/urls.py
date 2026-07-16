from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import UserLoginForm


app_name = "users"

urlpatterns = [
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html",
            authentication_form=UserLoginForm,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "profile/",
        views.CurrentUserProfileView.as_view(),
        name="profile",
    ),
    path(
        "profile/edit/",
        views.UserProfileUpdateView.as_view(),
        name="profile-edit",
    ),
    path(
        "users/<int:pk>/",
        views.UserProfileView.as_view(),
        name="profile-detail",
    ),
]
