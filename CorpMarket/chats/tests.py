from adverts.models import Advert
from chats.models import Chat, Message
from django.test import TestCase
from users.models import CustomUser


class ChatModelTest(TestCase):

    def setUp(self):
        self.seller = CustomUser.objects.create_user(username='chat_seller')
        self.buyer = CustomUser.objects.create_user(username='chat_buyer')
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


class MessageModelTest(TestCase):

    def setUp(self):
        seller = CustomUser.objects.create_user(username='message_seller')
        buyer = CustomUser.objects.create_user(username='message_buyer')
        advert = Advert.objects.create(
            seller=seller,
            title='Книги',
            description='Подборка книг по разработке.',
            category=Advert.Category.PRODUCT,
        )
        self.chat = Chat.objects.create(advert=advert, seller=seller, buyer=buyer)
        self.sender = buyer

    def test_message_creation_and_string_representation(self):
        message = Message.objects.create(chat=self.chat, sender=self.sender, text='123456789012345')

        self.assertEqual(str(message), f'Сообщение от message_buyer в чате {self.chat.pk}')
        self.assertEqual(message.get_preview(length=5), '12345...')
        self.assertFalse(message.is_read)

        message.mark_as_read()
        message.refresh_from_db()
        self.assertTrue(message.is_read)
