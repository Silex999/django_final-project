import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from booking.models import Booking, Computer, Zone


class Command(BaseCommand):
    help = 'Создаёт группы пользователей с правами доступа'

    def handle(self, *args, **kwargs):
        manager_group, created = Group.objects.get_or_create(
            name='Менеджер заявок'
        )
        booking_ct = ContentType.objects.get_for_model(Booking)
        computer_ct = ContentType.objects.get_for_model(Computer)
        zone_ct = ContentType.objects.get_for_model(Zone)

        manager_perms = Permission.objects.filter(
            content_type__in=[booking_ct, computer_ct, zone_ct],
            codename__in=[
                'view_booking', 'change_booking',  
                'view_computer',                     
                'view_zone',                         
            ]
        )
        manager_group.permissions.set(manager_perms)

        admin_group, _ = Group.objects.get_or_create(name='Администратор')
        all_perms = Permission.objects.filter(
            content_type__in=[booking_ct, computer_ct, zone_ct]
        )
        admin_group.permissions.set(all_perms)

        self.stdout.write(
            self.style.SUCCESS(
                'Группы "Менеджер заявок" и "Администратор" успешно созданы.'
            )
        )

        from django.contrib.auth.models import User
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@cafe.ru')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Суперпользователь "{admin_username}" создан.'
                )
            )