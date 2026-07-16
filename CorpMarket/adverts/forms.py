from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Advert, Photo


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 МБ


class AdvertPhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ("image",)
        widgets = {
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        # У уже сохранённого файла может не быть content_type.
        content_type = getattr(image, "content_type", None)

        if (
            content_type is not None
            and content_type not in ALLOWED_IMAGE_TYPES
        ):
            raise ValidationError(
                "Поддерживаются только изображения JPEG, PNG и WebP."
            )

        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError(
                "Размер фотографии не должен превышать 10 МБ."
            )

        return image


class BaseAdvertPhotoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        photo_count = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            uploaded_image = form.cleaned_data.get("image")
            existing_image = (
                form.instance.pk
                and bool(form.instance.image)
            )

            if uploaded_image or existing_image:
                photo_count += 1

        if photo_count < 1:
            raise ValidationError(
                "Добавьте минимум одну фотографию."
            )


AdvertPhotoFormSet = inlineformset_factory(
    Advert,
    Photo,
    form=AdvertPhotoForm,
    formset=BaseAdvertPhotoFormSet,
    fields=("image",),
    extra=0,
    min_num=1,
    validate_min=True,
    max_num=5,
    validate_max=True,
    can_delete=True,
)
