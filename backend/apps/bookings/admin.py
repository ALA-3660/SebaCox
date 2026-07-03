from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Booking, BookingStatusLog, Review


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'provider', 'service_category', 'status', 'scheduled_date', 'total_amount', 'is_paid', 'created_at']
    list_filter = ['status', 'is_paid', 'booking_type', 'urgency_level', 'scheduled_date', 'created_at']
    search_fields = ['id', 'customer__phone_number', 'provider__business_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'status_updated_at', 'accepted_at', 'started_at', 'completed_at', 'cancelled_at']
    fieldsets = (
        (_('Booking Information'), {
            'fields': ('id', 'customer', 'provider', 'status', 'booking_type')
        }),
        (_('Service Details'), {
            'fields': ('service_category', 'service_subcategory', 'description')
        }),
        (_('Location & Scheduling'), {
            'fields': ('booking_address', 'latitude', 'longitude', 'scheduled_date', 'scheduled_time', 'preferred_time_start', 'preferred_time_end')
        }),
        (_('Pricing'), {
            'fields': ('service_price', 'discount_amount', 'tax_amount', 'total_amount', 'currency', 'payment_method', 'is_paid')
        }),
        (_('Additional Info'), {
            'fields': ('urgency_level', 'special_requests', 'notes_to_provider', 'notes_from_provider')
        }),
        (_('Status Timeline'), {
            'fields': ('accepted_at', 'started_at', 'completed_at', 'cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'status_updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['from_status', 'to_status', 'created_at']
    search_fields = ['booking__id', 'changed_by__phone_number']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'reviewer', 'rating', 'would_recommend', 'helpful_count', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['booking__id', 'reviewer__phone_number', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
