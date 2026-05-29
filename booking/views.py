from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Computer, Zone, Booking
from .forms import BookingForm, BookingManagerForm


def index(request):
    zones = Zone.objects.all()
    total_computers = Computer.objects.filter(is_active=True).count()
    available_computers = Computer.objects.filter(
        is_active=True, status='available'
    ).count()
    total_bookings = Booking.objects.filter(status='completed').count()

    context = {
        'zones': zones,
        'total_computers': total_computers,
        'available_computers': available_computers,
        'total_bookings': total_bookings,
    }
    return render(request, 'index.html', context)


def computers_list(request):
    zone_id = request.GET.get('zone')
    computers = Computer.objects.filter(is_active=True).select_related('zone')
    zones = Zone.objects.all()

    if zone_id:
        computers = computers.filter(zone_id=zone_id)

    context = {
        'computers': computers,
        'zones': zones,
        'selected_zone': zone_id,
    }
    return render(request, 'booking/computers.html', context)


@login_required
def booking_create(request, computer_id):
    computer = get_object_or_404(Computer, pk=computer_id, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST, computer=computer)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.computer = computer
            booking.save()
            messages.success(
                request,
                f'Бронирование ПК №{computer.number} успешно создано!'
            )
            return redirect('booking_success', pk=booking.pk)
    else:
        form = BookingForm(computer=computer)

    context = {'form': form, 'computer': computer}
    return render(request, 'booking/booking_form.html', context)


@login_required
def booking_success(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'booking/booking_success.html', {'booking': booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('computer', 'computer__zone').order_by('-created_at')
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status in ('pending', 'confirmed'):
        if booking.start_time > timezone.now():
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Бронирование отменено.')
        else:
            messages.error(request, 'Нельзя отменить уже начавшийся сеанс.')
    else:
        messages.error(request, 'Невозможно отменить данное бронирование.')
    return redirect('my_bookings')


@login_required
def manager_bookings(request):
    user = request.user
    is_manager = (
        user.is_staff or
        user.groups.filter(name='Менеджер заявок').exists()
    )
    if not is_manager:
        messages.error(request, 'Доступ запрещён.')
        return redirect('index')

    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.all().select_related(
        'user', 'computer', 'computer__zone'
    )
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'booking/manager_bookings.html', context)


@login_required
def manager_booking_edit(request, pk):
    user = request.user
    is_manager = (
        user.is_staff or
        user.groups.filter(name='Менеджер заявок').exists()
    )
    if not is_manager:
        messages.error(request, 'Доступ запрещён.')
        return redirect('index')

    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingManagerForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус бронирования обновлён.')
            return redirect('manager_bookings')
    else:
        form = BookingManagerForm(instance=booking)

    context = {'form': form, 'booking': booking}
    return render(request, 'booking/manager_booking_edit.html', context)