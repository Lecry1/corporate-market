from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'photo',
            'address',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'photo': 'Фото профиля',
            'address': 'Адрес',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }

        for field_name, field in self.fields.items():
            field.label = labels[field_name]
            field.widget.attrs['class'] = 'form-control'
