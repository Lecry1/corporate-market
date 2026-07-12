from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from adverts.models import Advert
from reviews.models import Review

from .forms import UserProfileUpdateForm, UserRegisterForm


User = get_user_model()


class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("adverts:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        return response


class UserProfileView(DetailView):
    model = User
    template_name = "users/profile.html"
    context_object_name = "profile_user"

    def get_queryset(self):
        active_adverts = Advert.objects.filter(
            status=Advert.Status.ACTIVE,
        ).order_by("-created_at")

        completed_adverts = Advert.objects.filter(
            status=Advert.Status.COMPLETED,
        ).order_by("-created_at")

        archived_adverts = Advert.objects.filter(
            status=Advert.Status.ARCHIVED,
        ).order_by("-created_at")

        received_reviews = (
            Review.objects
            .select_related("from_user", "advert")
            .order_by("-created_at")
        )

        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "adverts",
                    queryset=active_adverts,
                    to_attr="active_adverts",
                ),
                Prefetch(
                    "adverts",
                    queryset=completed_adverts,
                    to_attr="completed_adverts",
                ),
                Prefetch(
                    "adverts",
                    queryset=archived_adverts,
                    to_attr="archived_adverts",
                ),
                Prefetch(
                    "reviews_received",
                    queryset=received_reviews,
                    to_attr="received_reviews",
                ),
            )
        )


class CurrentUserProfileView(
    LoginRequiredMixin,
    UserProfileView,
):
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        return queryset.get(pk=self.request.user.pk)


class UserProfileUpdateView(
    LoginRequiredMixin,
    UpdateView,
):
    form_class = UserProfileUpdateForm
    template_name = "users/profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("users:profile")
