from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class UserRegisterForm(UserCreationForm):
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

    def clean_email(self):
        email = self.cleaned_data["email"]

        if (
            User.objects
            .exclude(pk=self.instance.pk)
            .filter(email__iexact=email)
            .exists()
        ):
            raise forms.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email
