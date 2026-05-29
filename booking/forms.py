from django import forms
from django.utils import timezone
from .models import Booking, Computer


class BookingForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label='Начало сеанса',
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            },
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    end_time = forms.DateTimeField(
        label='Конец сеанса',
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            },
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    comment = forms.CharField(
        label='Комментарий (необязательно)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Любые пожелания...',
        }),
    )

    class Meta:
        model = Booking
        fields = ['start_time', 'end_time', 'comment']

    def __init__(self, *args, computer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.computer = computer

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if start and end:
            if start >= end:
                raise forms.ValidationError(
                    'Время начала должно быть раньше окончания.')
            if start < timezone.now():
                raise forms.ValidationError(
                    'Нельзя бронировать на прошедшее время.')
            duration = (end - start).total_seconds() / 3600
            if duration < 1:
                raise forms.ValidationError('Минимальное время сеанса — 1 час.')
            if duration > 24:
                raise forms.ValidationError('Максимальное время сеанса — 24 часа.')
            if self.computer and not self.computer.is_available_for(start, end):
                raise forms.ValidationError(
                    'Этот ПК уже занят на выбранное время. '
                    'Пожалуйста, выберите другое время.')
        return cleaned_data


class BookingManagerForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status', 'manager_note']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'manager_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }