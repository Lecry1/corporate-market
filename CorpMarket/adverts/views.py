from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.forms import inlineformset_factory
from django.http import Http404
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
    fields=("image", ),
    extra=1,
    max_num=5,
    validate_max=True,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class NotFoundOnPermissionMixin:

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        raise Http404


class AdvertPhotoFormsetDataMixin:

    def has_photo_formset_data(self):
        prefix = self.formset_class.get_default_prefix()
        return any(
            key.startswith(f"{prefix}-") for key in list(self.request.POST.keys()) + list(self.request.FILES.keys())
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
        return self.render_to_response(self.get_context_data(form=form, photo_formset=formset))

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
        category = self.request.GET.get("category", "").strip()
        status = self.request.GET.get(
            "status",
            Advert.Status.ACTIVE,
        ).strip()
        min_price = self.request.GET.get("min_price", "").strip()
        max_price = self.request.GET.get("max_price", "").strip()
        ordering = self.request.GET.get(
            "ordering",
            "-created_at",
        ).strip()

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))

        valid_categories = {value for value, _label in Advert.Category.choices}
        if category in valid_categories:
            queryset = queryset.filter(category=category)

        valid_statuses = {value for value, _label in Advert.Status.choices}
        if status != "all":
            if status not in valid_statuses:
                status = Advert.Status.ACTIVE

            queryset = queryset.filter(status=status)

        if min_price:
            try:
                queryset = queryset.filter(price__gte=int(min_price))
            except ValueError:
                pass

        if max_price:
            try:
                queryset = queryset.filter(price__lte=int(max_price))
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

        ordering_expressions = self._get_ordering_expressions(ordering)

        if status == "all":
            queryset = queryset.annotate(
                status_priority=Case(
                    When(
                        status=Advert.Status.ACTIVE,
                        then=Value(0),
                    ),
                    When(
                        status=Advert.Status.COMPLETED,
                        then=Value(1),
                    ),
                    When(
                        status=Advert.Status.ARCHIVED,
                        then=Value(2),
                    ),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )

            return queryset.order_by(
                "status_priority",
                *ordering_expressions,
            )

        return queryset.order_by(*ordering_expressions)

    @staticmethod
    def _get_ordering_expressions(ordering):
        """
        Возвращает безопасные выражения сортировки.

        Для цены значения NULL ("Договорная") всегда располагаются
        после объявлений с указанной ценой.
        """
        if ordering == "price":
            return (
                F("price").asc(nulls_last=True),
                F("created_at").desc(),
            )

        if ordering == "-price":
            return (
                F("price").desc(nulls_last=True),
                F("created_at").desc(),
            )

        if ordering == "created_at":
            return (F("created_at").asc(), )

        return (F("created_at").desc(), )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Advert.Category.choices
        context["statuses"] = Advert.Status.choices

        context["selected_status"] = self.request.GET.get(
            "status",
            Advert.Status.ACTIVE,
        )

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
    AdvertPhotoFormsetDataMixin,
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

        if form.is_valid():
            if self.has_photo_formset_data():
                photo_formset = self.get_formset()
                if not photo_formset.is_valid():
                    return self.render_invalid(form, photo_formset)

            form.instance.seller = self.request.user
            self.photo_formset = photo_formset if self.has_photo_formset_data() else None
            return self.form_valid(form)

        photo_formset = self.get_formset() if self.has_photo_formset_data() else None
        return self.render_invalid(form, photo_formset)

    def form_valid(self, form):
        response = super().form_valid(form)

        photo_formset = getattr(self, "photo_formset", None)
        if photo_formset is not None:
            photo_formset.instance = self.object
            photo_formset.save()

        return response


class AdvertUpdateView(
    LoginRequiredMixin,
    NotFoundOnPermissionMixin,
    AdvertPhotoFormSetMixin,
    AdvertPhotoFormsetDataMixin,
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

        if form.is_valid():
            if self.has_photo_formset_data():
                photo_formset = self.get_formset()
                if not photo_formset.is_valid():
                    return self.render_invalid(form, photo_formset)

            return self.form_valid(form)

        photo_formset = self.get_formset() if self.has_photo_formset_data() else None
        return self.render_invalid(form, photo_formset)

    def test_func(self):
        advert = self.get_object()

        return (advert.seller == self.request.user or self.request.user.is_superuser)

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class AdvertDeleteView(
    LoginRequiredMixin,
    NotFoundOnPermissionMixin,
    UserPassesTestMixin,
    DeleteView,
):
    model = Advert
    template_name = "adverts/advert_confirm_delete.html"
    success_url = reverse_lazy("adverts:list")

    def test_func(self):
        advert = self.get_object()

        return (advert.seller == self.request.user or self.request.user.is_superuser)
