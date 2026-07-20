from django import forms


class MessageForm(forms.Form):
    text = forms.CharField(
        label='Сообщение',
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите сообщение',
            },
        ),
    )

    def clean_text(self):
        text = self.cleaned_data['text'].strip()

        if not text:
            raise forms.ValidationError('Сообщение не может быть пустым.')

        return text
