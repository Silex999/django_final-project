from rest_framework import serializers
from .models import Computer, Zone, Booking
from django.contrib.auth.models import User


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'


class ComputerSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)
    zone_id = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.all(), source='zone', write_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Computer
        fields = [
            'id', 'number', 'zone', 'zone_id',
            'status', 'status_display',
            'cpu', 'gpu', 'ram', 'monitor',
            'image', 'is_active',
        ]


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    computer_number = serializers.IntegerField(
        source='computer.number', read_only=True
    )
    zone_name = serializers.CharField(
        source='computer.zone.name', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'computer', 'computer_number',
            'zone_name', 'start_time', 'end_time',
            'status', 'status_display', 'total_price',
            'comment', 'manager_note', 'duration_hours',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'user', 'total_price', 'status',
            'manager_note', 'created_at', 'updated_at',
        ]

    def validate(self, attrs):
        start = attrs.get('start_time')
        end = attrs.get('end_time')
        computer = attrs.get('computer')
        from django.utils import timezone

        if start and end:
            if start >= end:
                raise serializers.ValidationError(
                    'Время начала должно быть раньше окончания.')
            if start < timezone.now():
                raise serializers.ValidationError(
                    'Нельзя бронировать на прошедшее время.')
            duration = (end - start).total_seconds() / 3600
            if duration < 1:
                raise serializers.ValidationError('Минимум 1 час.')
            if computer:
                instance_id = self.instance.pk if self.instance else None
                qs = computer.bookings.filter(
                    status__in=['pending', 'confirmed'],
                    start_time__lt=end,
                    end_time__gt=start,
                )
                if instance_id:
                    qs = qs.exclude(pk=instance_id)
                if qs.exists():
                    raise serializers.ValidationError(
                        'ПК занят на выбранное время.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status', 'manager_note']