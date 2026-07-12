from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Case, F, IntegerField, Q, Value, When
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

        # Поиск по названию и описанию.
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
            )

        # Фильтрация по категории.
        valid_categories = {
            value for value, _label in Advert.Category.choices
        }

        if category in valid_categories:
            queryset = queryset.filter(category=category)

        # По умолчанию показываем только активные объявления.
        # Значение "all" означает вывод всех статусов.
        valid_statuses = {
            value for value, _label in Advert.Status.choices
        }

        if status != "all":
            if status not in valid_statuses:
                status = Advert.Status.ACTIVE

            queryset = queryset.filter(status=status)

        # Фильтрация по минимальной цене.
        if min_price:
            try:
                queryset = queryset.filter(
                    price__gte=int(min_price)
                )
            except ValueError:
                pass

        # Фильтрация по максимальной цене.
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

        ordering_expressions = self._get_ordering_expressions(ordering)

        # Если выбраны все статусы, сначала группируем объявления:
        # активные -> выполненные -> архивные.
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
            return (F("created_at").asc(),)

        return (F("created_at").desc(),)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Advert.Category.choices
        context["statuses"] = Advert.Status.choices

        # В шаблоне отсутствие параметра status означает
        # выбранный по умолчанию статус ACTIVE.
        context["selected_status"] = self.request.GET.get(
            "status",
            Advert.Status.ACTIVE,
        )

        # Сохраняем фильтры при переходе между страницами.
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


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
