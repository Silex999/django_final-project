from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import Computer, Zone, Booking
from .serializers import (
    ComputerSerializer, ZoneSerializer,
    BookingSerializer, BookingStatusSerializer,
)
from .permissions import IsAdminOrManager, IsAdminOrManagerOrReadOwn


class ZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]


class ComputerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Computer.objects.filter(is_active=True).select_related('zone')
    serializer_class = ComputerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['zone__name', 'zone__zone_type']

    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        computer = self.get_object()
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if not start or not end:
            return Response(
                {'error': 'Укажите параметры start и end (ISO 8601)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты'},
                status=status.HTTP_400_BAD_REQUEST
            )
        available = computer.is_available_for(start_dt, end_dt)
        return Response({'computer_id': computer.pk, 'available': available})


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAdminOrManagerOrReadOwn]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Менеджер заявок').exists():
            return Booking.objects.all().select_related(
                'user', 'computer', 'computer__zone'
            )
        return Booking.objects.filter(user=user).select_related(
            'computer', 'computer__zone'
        )

    @action(
        detail=True,
        methods=['patch'],
        url_path='change-status',
        permission_classes=[IsAdminOrManager],
    )
    def change_status(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingStatusSerializer(
            booking, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        url_path='my',
        permission_classes=[IsAuthenticated],
    )
    def my_bookings(self, request):
        bookings = Booking.objects.filter(
            user=request.user
        ).select_related('computer', 'computer__zone')
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)