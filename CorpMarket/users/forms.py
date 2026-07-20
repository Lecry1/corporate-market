from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


User = get_user_model()


class EmailUniqueValidationMixin:
    email_duplicate_error = (
        "Пользователь с таким email уже существует."
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        queryset = User.objects.filter(
            email__iexact=email,
        )

        instance = getattr(self, "instance", None)

        if instance and instance.pk:
            queryset = queryset.exclude(
                pk=instance.pk,
            )

        if queryset.exists():
            raise forms.ValidationError(
                self.email_duplicate_error
            )

        return email


class UserRegisterForm(EmailUniqueValidationMixin, UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update(
                {"class": "form-control"}
            )


class UserLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": (
            "Неверное имя пользователя или пароль."
        ),
        "inactive": (
            "Этот аккаунт отключён."
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "autofocus": True,
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
            }
        )


class UserProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "photo",
            "address",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "photo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Укажите адрес",
                }
            ),
        }
