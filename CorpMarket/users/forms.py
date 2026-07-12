from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    # Добавляем обязательное поле email (в стандартной форме оно опционально)
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")  # Сюда можно добавить и другие кастомные поля

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Автоматически добавляем CSS-классы Bootstrap 5 для всех полей формы
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})