from adverts.models import Advert
from chats.forms import MessageForm
from chats.models import Chat, Message
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.edit import FormMixin
from reviews.models import Review


class StartChatView(LoginRequiredMixin, FormView):
    form_class = MessageForm
    template_name = 'chats/chat_start.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.advert = get_object_or_404(Advert.objects.select_related('seller'), pk=kwargs['advert_pk'])

            existing_chat = Chat.objects.filter(
                advert=self.advert,
                buyer=request.user,
                seller=self.advert.seller,
            ).first()

            if existing_chat and request.method == 'GET':
                return redirect('chats:detail', pk=existing_chat.pk)

            if self.advert.seller_id == request.user.id:
                messages.error(request, 'Нельзя написать самому себе.')
                return redirect(self.advert)

            if self.advert.status != Advert.Status.ACTIVE:
                messages.error(request, 'Нельзя начать чат по неактивному объявлению.')
                return redirect(self.advert)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            chat, _ = Chat.objects.get_or_create(
                advert=self.advert,
                buyer=self.request.user,
                seller=self.advert.seller,
            )

            if not chat.is_active:
                messages.error(self.request, 'Чат закрыт. Отправка сообщений недоступна.')
                return redirect('chats:detail', pk=chat.pk)

            Message.objects.create(
                chat=chat,
                sender=self.request.user,
                text=form.cleaned_data['text'],
            )

        return redirect('chats:detail', pk=chat.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advert'] = self.advert
        return context


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chats/chat_list.html'
    context_object_name = 'chats'
    paginate_by = 20

    def get_queryset(self):
        latest_messages = Message.objects.filter(chat_id=OuterRef('pk')).order_by('-created_at')
        unread_filter = Q(messages__is_read=False) & ~Q(messages__sender_id=self.request.user.id)

        return (
            Chat.objects.filter(Q(buyer=self.request.user)
                                | Q(seller=self.request.user)).select_related('advert', 'buyer', 'seller').annotate(
                                    last_message_text=Subquery(latest_messages.values('text')[:1]),
                                    last_message_at=Subquery(latest_messages.values('created_at')[:1]),
                                    unread_message_count=Count('messages', filter=unread_filter),
                                ).order_by('-updated_at').select_related(
                                    "advert",
                                    "buyer",
                                    "seller",
                                ).prefetch_related("advert__photos")
        )


class ChatDetailView(LoginRequiredMixin, FormMixin, DetailView):
    model = Chat
    form_class = MessageForm
    template_name = 'chats/chat_detail.html'
    context_object_name = 'chat'

    def get_queryset(self):
        return (
            Chat.objects
            .filter(
                Q(buyer=self.request.user)
                | Q(seller=self.request.user)
            )
            .select_related(
                "advert",
                "buyer",
                "seller",
            )
            .prefetch_related("advert__photos")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_user = self.object.get_other_user(self.request.user)
        review_exists = Review.objects.filter(
            from_user=self.request.user,
            to_user=other_user,
            advert=self.object.advert,
        ).exists()

        message_queryset = self.object.messages.select_related('sender').order_by('-created_at')
        message_paginator = Paginator(message_queryset, 100)
        message_page = message_paginator.get_page(self.request.GET.get('page'))
        incoming_message_ids = [
            chat_message.pk for chat_message in message_page.object_list
            if chat_message.sender_id != self.request.user.id and not chat_message.is_read
        ]
        Message.objects.filter(pk__in=incoming_message_ids).update(is_read=True)
        context['chat_messages'] = list(reversed(message_page.object_list))
        context['message_page'] = message_page
        context['other_user'] = other_user
        context['can_leave_review'] = self.object.advert.status == Advert.Status.COMPLETED and not review_exists
        context['review_exists'] = review_exists
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.is_active:
            messages.error(request, 'Чат закрыт. Отправка сообщений недоступна.')
            return redirect('chats:detail', pk=self.object.pk)

        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        Message.objects.create(
            chat=self.object,
            sender=self.request.user,
            text=form.cleaned_data['text'],
        )
        return redirect('chats:detail', pk=self.object.pk)

    def get_success_url(self):
        return reverse('chats:detail', kwargs={'pk': self.object.pk})
