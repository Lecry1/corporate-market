from adverts.models import Advert
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)


class BootstrapFormMixin:

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field in form.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class

        return form


class AdvertListView(ListView):
    model = Advert
    template_name = 'adverts/advert_list.html'
    context_object_name = 'adverts'
    paginate_by = 6


class AdvertDetailView(DetailView):
    model = Advert
    template_name = 'adverts/advert_detail.html'
    context_object_name = 'advert'


class AdvertCreateView(BootstrapFormMixin, LoginRequiredMixin, CreateView):
    model = Advert
    template_name = 'adverts/advert_form.html'
    fields = (
        'title',
        'description',
        'price',
        'category',
        'address',
    )

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class AdvertUpdateView(
    BootstrapFormMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView,
):
    model = Advert
    template_name = 'adverts/advert_form.html'
    fields = (
        'title',
        'description',
        'price',
        'category',
        'status',
        'address',
    )

    def test_func(self):
        advert = self.get_object()
        return advert.seller == self.request.user or self.request.user.is_market_admin


class AdvertDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView,
):
    model = Advert
    template_name = 'adverts/advert_confirm_delete.html'
    success_url = reverse_lazy('adverts:list')

    def test_func(self):
        advert = self.get_object()
        return advert.seller == self.request.user or self.request.user.is_market_admin
