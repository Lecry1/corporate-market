from django import forms
from django.core.exceptions import ValidationError
from django.forms import (
    BaseInlineFormSet,
    inlineformset_factory,
)

from .models import Advert, Photo


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 МБ
MIN_PHOTO_COUNT = 1
MAX_PHOTO_COUNT = 5


class AdvertPhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ("image",)
        widgets = {
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": (
                        "image/jpeg,"
                        "image/png,"
                        "image/webp"
                    ),
                }
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        content_type = getattr(
            image,
            "content_type",
            None,
        )

        if (
            content_type is not None
            and content_type
            not in ALLOWED_IMAGE_CONTENT_TYPES
        ):
            raise ValidationError(
                "Поддерживаются только изображения "
                "JPEG, PNG и WebP."
            )

        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError(
                "Размер фотографии не должен "
                "превышать 10 МБ."
            )

        return image


class BaseAdvertPhotoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # При ошибках конкретных файлов показываем эти ошибки,
        # не добавляя поверх них ошибку количества фотографий.
        if any(form.errors for form in self.forms):
            return

        photo_count = 0

        for form in self.forms:
            cleaned_data = getattr(
                form,
                "cleaned_data",
                None,
            )

            if not cleaned_data:
                continue

            if cleaned_data.get("DELETE"):
                continue

            uploaded_image = cleaned_data.get("image")

            # При редактировании новый файл можно не выбирать:
            # в этом случае учитывается уже сохранённое изображение.
            existing_image = (
                form.instance.pk is not None
                and bool(form.instance.image)
            )

            if uploaded_image or existing_image:
                photo_count += 1

        if photo_count < MIN_PHOTO_COUNT:
            raise ValidationError(
                "Добавьте минимум одну фотографию."
            )

        if photo_count > MAX_PHOTO_COUNT:
            raise ValidationError(
                "Можно загрузить не более "
                "5 фотографий."
            )


AdvertPhotoFormSet = inlineformset_factory(
    parent_model=Advert,
    model=Photo,
    form=AdvertPhotoForm,
    formset=BaseAdvertPhotoFormSet,
    fields=("image",),
    extra=1,

    # Минимум проверяется вручную по реальному числу фото.
    min_num=0,
    validate_min=False,

    max_num=MAX_PHOTO_COUNT,
    validate_max=True,
    can_delete=True,
)
