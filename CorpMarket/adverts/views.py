from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db import transaction
from django.db.models import (
    Case,
    F,
    IntegerField,
    Q,
    Value,
    When,
)
from django.http import (
    Http404,
    HttpResponseRedirect,
    JsonResponse,
)
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import AdvertPhotoFormSet
from .models import Advert


class NotFoundOnPermissionMixin:
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        raise Http404


class AdvertPhotoFormSetMixin:
    formset_class = AdvertPhotoFormSet

    def get_formset(self):
        formset_kwargs = {
            "instance": self.object,
        }

        if self.request.method == "POST":
            formset_kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )

        return self.formset_class(
            **formset_kwargs
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            **kwargs
        )

        if "photo_formset" not in context:
            context["photo_formset"] = (
                self.get_formset()
            )

        return context

    def is_ajax_request(self):
        return (
            self.request.headers.get(
                "x-requested-with"
            )
            == "XMLHttpRequest"
        )

    @staticmethod
    def serialize_form_errors(form):
        serialized_errors = {}

        for field_name, errors in (
            form.errors.get_json_data().items()
        ):
            serialized_errors[field_name] = [
                error["message"]
                for error in errors
            ]

        return serialized_errors

    @staticmethod
    def serialize_formset_errors(
        photo_formset,
    ):
        form_errors = []

        for photo_form in photo_formset.forms:
            serialized_form_errors = {}

            for field_name, errors in (
                photo_form.errors
                .get_json_data()
                .items()
            ):
                serialized_form_errors[
                    field_name
                ] = [
                    error["message"]
                    for error in errors
                ]

            form_errors.append(
                serialized_form_errors
            )

        return {
            "forms": form_errors,
            "non_form_errors": [
                str(error)
                for error
                in photo_formset.non_form_errors()
            ],
        }

    def render_invalid_forms(
        self,
        form,
        photo_formset,
    ):
        if self.is_ajax_request():
            return JsonResponse(
                {
                    "success": False,
                    "form_errors": (
                        self.serialize_form_errors(
                            form
                        )
                    ),
                    "photo_formset_errors": (
                        self.serialize_formset_errors(
                            photo_formset
                        )
                    ),
                },
                status=400,
            )

        return self.render_to_response(
            self.get_context_data(
                form=form,
                photo_formset=photo_formset,
            )
        )

    def get_success_response(self):
        success_url = str(
            self.get_success_url()
        )

        if self.is_ajax_request():
            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": success_url,
                },
                status=201,
            )

        return HttpResponseRedirect(
            success_url
        )


class AdvertListView(ListView):
    model = Advert
    template_name = (
        "adverts/advert_list.html"
    )
    context_object_name = "adverts"
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()

        query = self.request.GET.get(
            "q",
            "",
        ).strip()

        category = self.request.GET.get(
            "category",
            "",
        ).strip()

        status = self.request.GET.get(
            "status",
            Advert.Status.ACTIVE,
        ).strip()

        min_price = self.request.GET.get(
            "min_price",
            "",
        ).strip()

        max_price = self.request.GET.get(
            "max_price",
            "",
        ).strip()

        ordering = self.request.GET.get(
            "ordering",
            "-created_at",
        ).strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(
                    description__icontains=query
                )
            )

        valid_categories = {
            value
            for value, _label
            in Advert.Category.choices
        }

        if category in valid_categories:
            queryset = queryset.filter(
                category=category
            )

        valid_statuses = {
            value
            for value, _label
            in Advert.Status.choices
        }

        if status != "all":
            if status not in valid_statuses:
                status = Advert.Status.ACTIVE

            queryset = queryset.filter(
                status=status
            )

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

        ordering_expressions = (
            self._get_ordering_expressions(
                ordering
            )
        )

        if status == "all":
            queryset = queryset.annotate(
                status_priority=Case(
                    When(
                        status=(
                            Advert.Status.ACTIVE
                        ),
                        then=Value(0),
                    ),
                    When(
                        status=(
                            Advert.Status.COMPLETED
                        ),
                        then=Value(1),
                    ),
                    When(
                        status=(
                            Advert.Status.ARCHIVED
                        ),
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

        return queryset.order_by(
            *ordering_expressions
        )

    @staticmethod
    def _get_ordering_expressions(
        ordering,
    ):
        if ordering == "price":
            return (
                F("price").asc(
                    nulls_last=True
                ),
                F("created_at").desc(),
            )

        if ordering == "-price":
            return (
                F("price").desc(
                    nulls_last=True
                ),
                F("created_at").desc(),
            )

        if ordering == "created_at":
            return (
                F("created_at").asc(),
            )

        return (
            F("created_at").desc(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            **kwargs
        )

        context["categories"] = (
            Advert.Category.choices
        )
        context["statuses"] = (
            Advert.Status.choices
        )
        context["selected_status"] = (
            self.request.GET.get(
                "status",
                Advert.Status.ACTIVE,
            )
        )

        query_params = (
            self.request.GET.copy()
        )
        query_params.pop("page", None)

        context["query_string"] = (
            query_params.urlencode()
        )

        return context


class AdvertDetailView(DetailView):
    model = Advert
    template_name = (
        "adverts/advert_detail.html"
    )
    context_object_name = "advert"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("seller")
            .prefetch_related("photos")
        )


class AdvertCreateView(
    LoginRequiredMixin,
    AdvertPhotoFormSetMixin,
    CreateView,
):
    model = Advert
    template_name = (
        "adverts/advert_form.html"
    )
    fields = (
        "title",
        "description",
        "price",
        "category",
        "address",
    )

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        self.object = None

        form = self.get_form()
        photo_formset = self.get_formset()

        form_is_valid = form.is_valid()
        photo_formset_is_valid = (
            photo_formset.is_valid()
        )

        if (
            not form_is_valid
            or not photo_formset_is_valid
        ):
            return self.render_invalid_forms(
                form,
                photo_formset,
            )

        return self.forms_valid(
            form,
            photo_formset,
        )

    def forms_valid(
        self,
        form,
        photo_formset,
    ):
        with transaction.atomic():
            form.instance.seller = (
                self.request.user
            )
            self.object = form.save()

            photo_formset.instance = (
                self.object
            )
            photo_formset.save()

        return self.get_success_response()


class AdvertUpdateView(
    LoginRequiredMixin,
    NotFoundOnPermissionMixin,
    AdvertPhotoFormSetMixin,
    UserPassesTestMixin,
    UpdateView,
):
    model = Advert
    template_name = (
        "adverts/advert_form.html"
    )
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
            advert.seller
            == self.request.user
            or self.request.user.is_superuser
        )

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        self.object = self.get_object()

        form = self.get_form()
        photo_formset = self.get_formset()

        form_is_valid = form.is_valid()
        photo_formset_is_valid = (
            photo_formset.is_valid()
        )

        if (
            not form_is_valid
            or not photo_formset_is_valid
        ):
            return self.render_invalid_forms(
                form,
                photo_formset,
            )

        return self.forms_valid(
            form,
            photo_formset,
        )

    def forms_valid(
        self,
        form,
        photo_formset,
    ):
        with transaction.atomic():
            self.object = form.save()

            photo_formset.instance = (
                self.object
            )
            photo_formset.save()

        return self.get_success_response()


class AdvertDeleteView(
    LoginRequiredMixin,
    NotFoundOnPermissionMixin,
    UserPassesTestMixin,
    DeleteView,
):
    model = Advert
    template_name = (
        "adverts/advert_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "adverts:list"
    )

    def test_func(self):
        advert = self.get_object()

        return (
            advert.seller
            == self.request.user
            or self.request.user.is_superuser
        )
