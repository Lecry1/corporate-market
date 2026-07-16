from adverts.models import Advert
from chats.models import Chat
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView
from reviews.forms import ReviewForm
from reviews.models import Review

User = get_user_model()


class ReviewCreateView(LoginRequiredMixin, CreateView):
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            participant_filter = Q(buyer=request.user) | Q(seller=request.user)
            self.chat = get_object_or_404(
                Chat.objects.filter(participant_filter).select_related('advert', 'buyer', 'seller'),
                pk=kwargs['chat_pk'],
            )
            self.reviewed_user = self.chat.get_other_user(request.user)

            if not self.chat.has_two_way_communication():
                messages.error(
                    request,
                    (
                        "Оставить отзыв можно только после общения: "
                        "покупатель и продавец должны отправить "
                        "хотя бы по одному сообщению."
                    ),
                )
                return redirect("chats:detail",pk=self.chat.pk,)

            # if self.chat.advert.status != Advert.Status.COMPLETED:
            #     messages.error(request, 'Отзыв можно оставить только после завершения сделки.')
            #     return redirect('chats:detail', pk=self.chat.pk)

            if Review.objects.filter(
                from_user=request.user,
                to_user=self.reviewed_user,
                advert=self.chat.advert,
            ).exists():
                messages.info(request, 'Вы уже оставили отзыв этому пользователю по объявлению.')
                return redirect('chats:detail', pk=self.chat.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.from_user = self.request.user
        form.instance.to_user = self.reviewed_user
        form.instance.advert = self.chat.advert
        form.instance.flag = (
            Review.Flag.TO_SELLER if self.reviewed_user == self.chat.advert.seller else Review.Flag.TO_BUYER
        )

        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            messages.info(self.request, 'Вы уже оставили отзыв этому пользователю по объявлению.')
            return redirect('chats:detail', pk=self.chat.pk)
        except ValidationError as error:
            form.add_error(None, ' '.join(error.messages))
            return self.form_invalid(form)

        messages.success(self.request, 'Отзыв опубликован.')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chat'] = self.chat
        context['reviewed_user'] = self.reviewed_user
        return context

    def get_success_url(self):
        return reverse('chats:detail', kwargs={'pk': self.chat.pk})


class UserReviewListView(ListView):
    model = Review
    template_name = 'reviews/user_review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        self.review_user = get_object_or_404(User, pk=self.kwargs['user_pk'])
        return Review.objects.filter(to_user=self.review_user).select_related('from_user', 'to_user', 'advert')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_user'] = self.review_user
        return context


class AdvertReviewListView(ListView):
    model = Review
    template_name = 'reviews/advert_review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        self.advert = get_object_or_404(Advert.objects.select_related('seller'), pk=self.kwargs['advert_pk'])
        return Review.objects.filter(advert=self.advert).select_related('from_user', 'to_user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advert'] = self.advert
        return context
