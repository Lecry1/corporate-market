from django import forms
from reviews.models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label='Оценка',
        choices=[(rating, str(rating)) for rating in range(1, 6)],
        coerce=int,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment':
            forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Расскажите, как прошла сделка',
                },
            ),
        }
