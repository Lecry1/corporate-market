from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.forms import inlineformset_factory
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Advert, Photo


AdvertPhotoFormSet = inlineformset_factory(
    Advert,
    Photo,
    fields=("image",),
    extra=1,
    max_num=5,
    validate_max=True,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class AdvertPhotoFormSetMixin:
    formset_class = AdvertPhotoFormSet

    def get_formset(self):
        if self.request.method == "POST":
            return self.formset_class(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
            )

        return self.formset_class(instance=self.object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("photo_formset", self.get_formset())
        return context

    def render_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, photo_formset=formset)
        )

    def form_valid(self, form):
        photo_formset = self.get_formset()

        if not photo_formset.is_valid():
            return self.render_invalid(form, photo_formset)

        response = super().form_valid(form)
        photo_formset.instance = self.object
        photo_formset.save()
        return response


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Advert.Category.choices

        query_params = self.request.GET.copy()
        query_params.pop("page", None)

        context["query_string"] = query_params.urlencode()

        return context


class AdvertDetailView(DetailView):
    model = Advert
    template_name = "adverts/advert_detail.html"
    context_object_name = "advert"


class AdvertCreateView(
    LoginRequiredMixin,
    AdvertPhotoFormSetMixin,
    CreateView,
):
    model = Advert
    template_name = "adverts/advert_form.html"
    fields = (
        "title",
        "description",
        "price",
        "category",
        "address",
    )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        photo_formset = self.get_formset()

        if form.is_valid() and photo_formset.is_valid():
            form.instance.seller = self.request.user
            return self.form_valid(form)

        return self.render_invalid(form, photo_formset)


class AdvertUpdateView(
    LoginRequiredMixin,
    AdvertPhotoFormSetMixin,
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        photo_formset = self.get_formset()

        if form.is_valid() and photo_formset.is_valid():
            return self.form_valid(form)

        return self.render_invalid(form, photo_formset)

    def test_func(self):
        advert = self.get_object()
        return (
            advert.seller == self.request.user
            or self.request.user.is_superuser
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


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
