from django.urls import path, include

urlpatterns = [
    path('core/', include('apps.core.urls', namespace='core')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('bookings/', include('apps.bookings.urls', namespace='bookings')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
]
