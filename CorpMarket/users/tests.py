from django.test import TestCase
from users.models import Admin, CustomUser


class CustomUserModelTest(TestCase):

    def test_user_creation_and_string_representation(self):
        password = 'safe-password-2026'
        user = CustomUser.objects.create_user(
            username='alex',
            password=password,
            first_name='Александр',
            last_name='Гущин',
        )

        self.assertEqual(str(user), 'alex')
        self.assertEqual(user.display_name, 'Александр Гущин')
        self.assertEqual(user.buyer_rating, 0.0)
        self.assertEqual(user.seller_rating, 0.0)
        self.assertTrue(user.check_password(password))


class AdminModelTest(TestCase):

    def test_admin_creation_and_string_representation(self):
        user = CustomUser.objects.create_user(username='administrator')
        administrator = Admin.objects.create(user=user)

        self.assertEqual(administrator.pk, user.pk)
        self.assertEqual(administrator.user, user)
        self.assertEqual(user.admin_profile, administrator)
        self.assertTrue(user.is_market_admin)
        self.assertEqual(str(administrator), 'Администратор administrator')
