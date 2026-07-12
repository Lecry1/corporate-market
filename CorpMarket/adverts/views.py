from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Advert


class AdvertListView(ListView):
    model = Advert
    template_name = "adverts/advert_list.html"
    context_object_name = "adverts"
    paginate_by = 6


class AdvertDetailView(DetailView):
    model = Advert
    template_name = "adverts/advert_detail.html"
    context_object_name = "advert"


class AdvertCreateView(LoginRequiredMixin, CreateView):
    model = Advert
    template_name = "adverts/advert_form.html"
    fields = (
        "title",
        "description",
        "price",
        "category",
        "address",
    )

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class AdvertUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView,
):
    model = Advert
    template_name = "adverts/advert_form.html"
    fields = (
        "title",
        "description",
        "price",
        "category",
        "status",
        "address",
    )

    def test_func(self):
        advert = self.get_object()
        return (
            advert.seller == self.request.user
            or self.request.user.is_superuser
        )


class AdvertDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView,
):
    model = Advert
    template_name = "adverts/advert_confirm_delete.html"
    success_url = reverse_lazy("adverts:list")

    def test_func(self):
        advert = self.get_object()
        return (
            advert.seller == self.request.user
            or self.request.user.is_superuser
        )
