from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Zone(models.Model):
    ZONE_TYPES = [
        ('standard', 'Стандарт'),
        ('vip', 'VIP'),
        ('pro', 'Про-геймер'),
    ]
    name = models.CharField('Название зоны', max_length=100)
    zone_type = models.CharField('Тип зоны', max_length=20,
                                  choices=ZONE_TYPES, default='standard')
    description = models.TextField('Описание', blank=True)
    price_per_hour = models.DecimalField('Цена/час (₽)',
                                          max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Зона'
        verbose_name_plural = 'Зоны'

    def __str__(self):
        return f"{self.name} ({self.get_zone_type_display()})"


class Computer(models.Model):
    STATUS_CHOICES = [
        ('available', 'Свободен'),
        ('booked', 'Забронирован'),
        ('maintenance', 'Обслуживание'),
    ]
    number = models.PositiveIntegerField('Номер ПК', unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,
                              related_name='computers',
                              verbose_name='Зона')
    status = models.CharField('Статус', max_length=20,
                               choices=STATUS_CHOICES, default='available')
    cpu = models.CharField('Процессор', max_length=100, blank=True)
    gpu = models.CharField('Видеокарта', max_length=100, blank=True)
    ram = models.CharField('ОЗУ', max_length=50, blank=True)
    monitor = models.CharField('Монитор', max_length=100, blank=True)
    image = models.ImageField('Фото', upload_to='computers/',
                               blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Компьютер'
        verbose_name_plural = 'Компьютеры'
        ordering = ['number']

    def __str__(self):
        return f"ПК №{self.number} — {self.zone.name}"

    def is_available_for(self, start_dt, end_dt):
        overlapping = self.bookings.filter(
            status__in=['pending', 'confirmed'],
            start_time__lt=end_dt,
            end_time__gt=start_dt,
        )
        return not overlapping.exists()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='bookings',
                              verbose_name='Пользователь')
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE,
                                  related_name='bookings',
                                  verbose_name='Компьютер')
    start_time = models.DateTimeField('Начало сеанса')
    end_time = models.DateTimeField('Конец сеанса')
    status = models.CharField('Статус', max_length=20,
                               choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField('Итого (₽)', max_digits=10,
                                       decimal_places=2, default=0)
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    manager_note = models.TextField('Заметка менеджера', blank=True)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return (f"Бронь #{self.pk} — {self.user.username} "
                f"| ПК №{self.computer.number} "
                f"| {self.start_time.strftime('%d.%m.%Y %H:%M')}")

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(
                    'Время начала должно быть раньше времени окончания.')
            if self.start_time < timezone.now():
                raise ValidationError(
                    'Нельзя бронировать на прошедшее время.')
            duration = (self.end_time - self.start_time).total_seconds() / 3600
            if duration < 1:
                raise ValidationError('Минимальное время — 1 час.')
            if duration > 24:
                raise ValidationError('Максимальное время — 24 часа.')

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            duration_hours = (
                (self.end_time - self.start_time).total_seconds() / 3600
            )
            self.total_price = (
                self.computer.zone.price_per_hour * duration_hours
            )
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        delta = self.end_time - self.start_time
        return round(delta.total_seconds() / 3600, 1)