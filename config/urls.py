from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "CyberCafe - Администрирование"
admin.site.site_title = "CyberCafe Admin"
admin.site.index_title = "Панель управления"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('booking.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)