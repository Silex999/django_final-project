from django.contrib import admin
from django.utils.html import format_html
from .models import Zone, Computer, Booking


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone_type', 'price_per_hour']
    list_filter = ['zone_type']
    search_fields = ['name']


@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ['number', 'zone', 'status', 'cpu', 'gpu', 'is_active']
    list_filter = ['zone', 'status', 'is_active']
    search_fields = ['number', 'cpu', 'gpu']
    list_editable = ['status', 'is_active']


class BookingStatusFilter(admin.SimpleListFilter):
    title = 'Статус'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Booking.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'computer_info', 'start_time',
        'end_time', 'duration_hours', 'total_price_display',
        'status_badge', 'created_at',
    ]
    list_filter = [BookingStatusFilter, 'computer__zone', 'created_at']
    search_fields = [
        'user__username', 'user__email',
        'computer__number', 'comment',
    ]
    readonly_fields = [
        'user', 'computer', 'start_time', 'end_time',
        'total_price', 'created_at', 'updated_at',
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Информация о бронировании', {
            'fields': (
                'user', 'computer', 'start_time',
                'end_time', 'total_price', 'comment',
            )
        }),
        ('Управление (менеджер)', {
            'fields': ('status', 'manager_note'),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser and request.user.groups.filter(
            name='Менеджер заявок'
        ).exists():
            return [
                f.name for f in self.model._meta.fields
                if f.name not in ('status', 'manager_note')
            ]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Менеджер заявок').exists():
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Менеджер заявок').exists():
            return False
        return super().has_add_permission(request)

    @admin.display(description='Пользователь')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.pk, obj.user.username
        )

    @admin.display(description='Компьютер')
    def computer_info(self, obj):
        return f"ПК №{obj.computer.number} ({obj.computer.zone.name})"

    @admin.display(description='Длительность')
    def duration_hours(self, obj):
        return f"{obj.duration_hours} ч."

    @admin.display(description='Сумма')
    def total_price_display(self, obj):
        return f"{obj.total_price} ₽"

    @admin.display(description='Статус')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#198754',
            'cancelled': '#dc3545',
            'completed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )