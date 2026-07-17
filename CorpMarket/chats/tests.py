from adverts.models import Advert
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Chat, Message

User = get_user_model()


class ChatModelTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(username='chat_seller')
        self.buyer = User.objects.create_user(username='chat_buyer')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Кофемашина',
            description='Автоматическая кофемашина.',
            category=Advert.Category.PRODUCT,
        )

    def test_chat_creation_and_string_representation(self):
        chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)

        expected = "Чат по 'Кофемашина' между chat_buyer и chat_seller"
        self.assertEqual(str(chat), expected)
        self.assertEqual(chat.get_other_user(self.buyer), self.seller)
        self.assertEqual(chat.get_other_user(self.seller), self.buyer)
        self.assertTrue(Chat.objects.filter(pk=chat.pk).exists())

    def test_chat_get_unread_count(self):
        chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)
        Message.objects.create(chat=chat, sender=self.seller, text='Привет!', is_read=False)
        Message.objects.create(chat=chat, sender=self.seller, text='Как дела?', is_read=False)
        self.assertEqual(chat.get_unread_count(self.buyer), 2)
        self.assertEqual(chat.get_unread_count(self.seller), 0)


class MessageModelTest(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(username='message_seller')
        self.buyer = User.objects.create_user(username='message_buyer')
        self.advert = Advert.objects.create(
            seller=self.seller,
            title='Книги',
            description='Подборка книг по разработке.',
            category=Advert.Category.PRODUCT,
        )
        self.chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)
        self.sender = self.buyer

    def test_message_creation_and_string_representation(self):
        message = Message.objects.create(chat=self.chat, sender=self.sender, text='123456789012345')

        self.assertEqual(str(message), f'Сообщение от message_buyer в чате {self.chat.pk}')
        self.assertEqual(message.get_preview(length=5), '12345...')
        self.assertFalse(message.is_read)

        message.mark_as_read()
        message.refresh_from_db()
        self.assertTrue(message.is_read)


class ChatViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='sellerpass123')
        self.buyer = User.objects.create_user(username='buyer', password='buyerpass123')
        self.other_user = User.objects.create_user(username='other', password='otherpass123')
        self.advert = Advert.objects.create(
            seller=self.seller, title='Тестовое объявление', description='Описание', price=1000,
            category=Advert.Category.PRODUCT, address='Москва'
        )
        self.chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=self.buyer)

    def test_chat_list_authenticated(self):
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chats/list.html')

    def test_chat_list_unauthenticated_redirect(self):
        response = self.client.get(reverse('chats:list'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={reverse("chats:list")}')

    def test_chat_list_shows_only_user_chats(self):
        other_user = User.objects.create_user(username='other2')
        other_chat = Chat.objects.create(advert=self.advert, seller=self.seller, buyer=other_user)

        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:list'))
        chats = response.context['chats']
        self.assertIn(self.chat, chats)
        self.assertNotIn(other_chat, chats)

    def test_chat_list_shows_unread_count(self):
        Message.objects.create(chat=self.chat, sender=self.seller, text='Привет!', is_read=False)
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:list'))
        self.assertContains(response, '1')

    def test_chat_detail_authenticated(self):
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chats/detail.html')

    def test_chat_detail_unauthenticated_redirect(self):
        response = self.client.get(reverse('chats:detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 302)

    def test_chat_detail_other_user_forbidden(self):
        self.client.login(username='other', password='otherpass123')
        response = self.client.get(reverse('chats:detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 404)

    def test_chat_detail_marks_messages_as_read(self):
        Message.objects.create(chat=self.chat, sender=self.seller, text='Привет!', is_read=False)
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 200)
        message = Message.objects.first()
        self.assertTrue(message.is_read)

    def test_create_chat_authenticated_success(self):
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:create', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Chat.objects.filter(advert=self.advert, buyer=self.buyer, seller=self.seller).exists())

    def test_create_chat_unauthenticated_redirect(self):
        response = self.client.get(reverse('chats:create', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)

    def test_create_chat_with_self_forbidden(self):
        self.client.login(username='seller', password='sellerpass123')
        response = self.client.get(reverse('chats:create', args=[self.advert.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Chat.objects.filter(advert=self.advert).exists())

    def test_send_message_authenticated_success(self):
        self.client.login(username='buyer', password='buyerpass123')
        data = {'text': 'Привет! Как дела?'}
        response = self.client.post(reverse('chats:send', args=[self.chat.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(chat=self.chat, sender=self.buyer, text='Привет! Как дела?').exists())

    def test_send_message_unauthenticated_redirect(self):
        data = {'text': 'Привет!'}
        response = self.client.post(reverse('chats:send', args=[self.chat.pk]), data)
        self.assertEqual(response.status_code, 302)

    def test_send_message_other_user_forbidden(self):
        self.client.login(username='other', password='otherpass123')
        data = {'text': 'Привет!'}
        response = self.client.post(reverse('chats:send', args=[self.chat.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(chat=self.chat).exists())

    def test_send_message_empty_forbidden(self):
        self.client.login(username='buyer', password='buyerpass123')
        data = {'text': ''}
        response = self.client.post(reverse('chats:send', args=[self.chat.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(chat=self.chat).exists())

    def test_send_message_ajax_success(self):
        self.client.login(username='buyer', password='buyerpass123')
        data = {'text': 'AJAX сообщение'}
        response = self.client.post(
            reverse('chats:send', args=[self.chat.pk]), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['message'], 'AJAX сообщение')
        self.assertTrue(Message.objects.filter(chat=self.chat, sender=self.buyer, text='AJAX сообщение').exists())

    def test_send_message_ajax_empty(self):
        self.client.login(username='buyer', password='buyerpass123')
        data = {'text': ''}
        response = self.client.post(
            reverse('chats:send', args=[self.chat.pk]), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    def test_unread_count_authenticated(self):
        Message.objects.create(chat=self.chat, sender=self.seller, text='Привет!', is_read=False)
        Message.objects.create(chat=self.chat, sender=self.seller, text='Как дела?', is_read=False)
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('messages:unread_count'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 2)

    def test_unread_count_unauthenticated(self):
        response = self.client.get(reverse('messages:unread_count'))
        self.assertEqual(response.status_code, 302)

    def test_close_chat_authenticated_success(self):
        self.client.login(username='buyer', password='buyerpass123')
        response = self.client.get(reverse('chats:close', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 302)
        self.chat.refresh_from_db()
        self.assertFalse(self.chat.is_active)

    def test_close_chat_unauthenticated_redirect(self):
        response = self.client.get(reverse('chats:close', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 302)

    def test_close_chat_other_user_forbidden(self):
        self.client.login(username='other', password='otherpass123')
        response = self.client.get(reverse('chats:close', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 302)
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_active)
