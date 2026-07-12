from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import F, Q
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

    def get_queryset(self):
        queryset = super().get_queryset()

        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "")
        min_price = self.request.GET.get("min_price", "")
        max_price = self.request.GET.get("max_price", "")
        ordering = self.request.GET.get("ordering", "-created_at")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
            )

        if category:
            queryset = queryset.filter(category=category)

        if min_price:
            try:
                queryset = queryset.filter(
                    price__gte=int(min_price)
                )
            except ValueError:
                pass

        if max_price:
            try:
                queryset = queryset.filter(
                    price__lte=int(max_price)
                )
            except ValueError:
                pass

        allowed_orderings = {
            "created_at",
            "-created_at",
            "price",
            "-price",
        }

        if ordering not in allowed_orderings:
            ordering = "-created_at"

        if ordering == "price":
            return queryset.order_by(
                F("price").asc(nulls_last=True)
            )

        if ordering == "-price":
            return queryset.order_by(
                F("price").desc(nulls_last=True)
            )

        return queryset.order_by(ordering)


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
