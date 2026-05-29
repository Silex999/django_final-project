from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('computers/', views.computers_list, name='computers_list'),
    path('computers/<int:computer_id>/book/',
         views.booking_create, name='booking_create'),
    path('booking/<int:pk>/success/',
         views.booking_success, name='booking_success'),
    path('booking/<int:pk>/cancel/',
         views.booking_cancel, name='booking_cancel'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('manager/bookings/', views.manager_bookings, name='manager_bookings'),
    path('manager/bookings/<int:pk>/edit/',
         views.manager_booking_edit, name='manager_booking_edit'),
]